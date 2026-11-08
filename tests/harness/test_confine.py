"""Staying in the workspace: file tools in the provider's workspaces, and `ws_run` in the peer's folder, with no push and a time limit (REQ-HARNESS-008)."""

import asyncio
import os
import sys
import time
from pathlib import Path

import pytest

from harness.scripted import ScriptedModel, call, chat, commit_all, git_out, head, peer_id
from specworks.harness import workspaces
from specworks.harness.confine import refuses
from specworks.harness.workspaces import SpecworksWorktrees

PYTHON = f'"{sys.executable}"'
#: A command that leaves the file `ran` in its folder, on every platform's shell.
MARK = f"{PYTHON} -c \"open('ran', 'w').close()\""


def ask(name, text):
    async def then(session, user):
        await user.say(text, to=peer_id(session, name))

    return then


def results(model, peer):
    """Every tool result the peer's last model call was given."""
    return model.runs_of(peer)[-1].tool_results()


def worktree_folder(project):
    """The folder of `test`'s worktree."""
    for line in git_out(project, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            folder = Path(line.removeprefix("worktree "))
        elif line == "branch refs/heads/peer/test":
            return folder.resolve()
    raise AssertionError("no worktree on peer/test")


@pytest.fixture
def outside(tmp_path_factory):
    """A file outside the project."""
    path = tmp_path_factory.mktemp("outside") / "outside.txt"
    path.write_text("secret\n", encoding="utf-8")
    return path


# @ac AC-HARNESS-008.1
def test_ac_harness_008_1_outside_the_workspace(project, ws, outside):
    escape = os.path.relpath(outside, project).replace(os.sep, "/")  # ../<...>/outside.txt
    written = outside.parent / "written.txt"
    model = ScriptedModel(
        script={
            "refine": [
                call("read_file", file_path="/../outside.txt"),
                call("read_file", file_path="/" + escape),
                call("write_file", file_path="/" + os.path.relpath(written, project).replace(os.sep, "/"), content="x"),
                call("edit_file", file_path="/" + escape, old_string="secret", new_string="changed"),
                call("read_file", file_path=str(outside)),
                call("write_file", file_path=str(written), content="x"),
                "done",
            ]
        }
    )
    chat(ws, model, then=ask("refine", "look around"))
    found = results(model, "refine")
    assert len(found) == 6
    assert all("error" in result.lower() for result in found[:4]), found
    assert not any("secret" in result for result in found)
    assert outside.read_text(encoding="utf-8") == "secret\n"
    assert not written.exists()


# @ac AC-HARNESS-008.1
def test_ac_harness_008_1_a_link_that_leads_outside(project, ws, outside):
    try:
        (project / "link").symlink_to(outside.parent, target_is_directory=True)
    except OSError:
        pytest.skip("symbolic links cannot be made here")
    model = ScriptedModel(script={"refine": [call("read_file", file_path="/link/outside.txt"), call("write_file", file_path="/link/new.txt", content="x"), "done"]})
    chat(ws, model, then=ask("refine", "follow the link"))
    found = results(model, "refine")
    assert len(found) == 2 and all("error" in result.lower() for result in found), found
    assert not any("secret" in result for result in found)
    assert not (outside.parent / "new.txt").exists()


# @ac AC-HARNESS-008.1
def test_ac_harness_008_1_inside_still_works(project, ws):
    model = ScriptedModel(script={"refine": [call("write_file", file_path="/inside.txt", content="inside\n"), call("read_file", file_path="/inside.txt"), "done"]})
    chat(ws, model, then=ask("refine", "write inside"))
    assert (project / "inside.txt").read_text(encoding="utf-8") == "inside\n"
    assert "inside" in results(model, "refine")[-1]


# @ac AC-HARNESS-008.2
def test_ac_harness_008_2_the_commands_folder(project, ws):
    model = ScriptedModel(script={"test": [call("ws_run", command=f'{PYTHON} -c "import os; print(os.getcwd())"'), "done"]})
    chat(ws, model, then=ask("test", "where are you?"))
    [result] = results(model, "test")
    first, *output = result.strip().splitlines()
    assert first == "exit code 0"
    assert Path(output[-1].strip()).resolve() == worktree_folder(project)
    assert worktree_folder(project) != project.resolve()


# @ac AC-HARNESS-008.2
def test_ac_harness_008_2_a_phase_peer_runs_in_the_checkout(project, ws):
    async def main():
        checkout = await SpecworksWorktrees(ws).provision("refine", "refine")
        return await checkout.run(f'{PYTHON} -c "import os; print(os.getcwd())"')

    first, *output = asyncio.run(main()).strip().splitlines()
    assert first == "exit code 0"
    assert Path(output[-1].strip()).resolve() == project.resolve()


async def run_in_checkout(ws, command):
    checkout = await SpecworksWorktrees(ws).provision("refine", "refine")
    return await checkout.run(command)


# @ac AC-HARNESS-008.3
@pytest.mark.parametrize("push", ["git push", "git push origin main", "git -C . push"])
def test_ac_harness_008_3_no_push(project, ws, push):
    before = head(project)
    command = f"{MARK} && {push}"
    assert refuses(command)
    with pytest.raises(PermissionError) as error:
        asyncio.run(run_in_checkout(ws, command))
    assert "git push is refused" in str(error.value)
    assert not (project / "ran").exists(), "nothing runs"
    assert head(project) == before


# @ac AC-HARNESS-008.3
def test_ac_harness_008_3_the_agent_sees_the_refusal(project, ws):
    model = ScriptedModel(script={"refine": [call("ws_run", command=f"{MARK} && git push origin main"), "done"]})
    chat(ws, model, then=ask("refine", "push it"))
    [result] = results(model, "refine")
    assert result.startswith("ws_run failed: PermissionError")
    assert "git push is refused" in result
    assert not (project / "ran").exists()


# @ac AC-HARNESS-008.3
def test_ac_harness_008_3_other_git_commands_run(project, ws):
    (project / "tracked.txt").write_text("one\n", encoding="utf-8")
    commit_all(project, "tracked")
    (project / "tracked.txt").write_text("two\n", encoding="utf-8")
    assert not refuses("git stash push -m wip") and not refuses('git commit -m "push later"')
    stashed = asyncio.run(run_in_checkout(ws, "git stash push -m wip"))
    assert stashed.startswith("exit code 0")
    assert "wip" in git_out(project, "stash", "list")
    (project / "new.txt").write_text("new\n", encoding="utf-8")
    git_out(project, "add", "new.txt")
    committed = asyncio.run(run_in_checkout(ws, 'git commit -m "push later"'))
    assert committed.startswith("exit code 0")
    assert git_out(project, "log", "-1", "--format=%s").strip() == "push later"


# @ac AC-HARNESS-008.4
def test_ac_harness_008_4_another_peers_workspace(project, ws):
    async def provision():
        return (await SpecworksWorktrees(ws).provision("test", "test")).tree.root

    folder = asyncio.run(provision())
    model = ScriptedModel(script={"build": [call("write_file", file_path="/peers/test/x.py", content="x = 1\n"), "done"]})
    chat(ws, model, then=ask("build", "write in test's workspace"))
    [result] = results(model, "build")
    assert "read-only" in result
    assert not (folder / "x.py").exists()
    assert git_out(folder, "status", "--porcelain", "--untracked-files=all").strip() == ""


# @ac AC-HARNESS-008.5
def test_ac_harness_008_5_a_command_that_runs_too_long(project, ws, monkeypatch):
    monkeypatch.setattr(workspaces, "RUN_TIMEOUT", 0.5)
    late = project / "finished"
    command = f"{PYTHON} -c \"import time; time.sleep(2); open('finished', 'w').close()\""
    model = ScriptedModel(script={"refine": [call("ws_run", command=command), "done"]})
    started = time.monotonic()
    chat(ws, model, then=ask("refine", "wait"))
    [result] = results(model, "refine")
    assert result.startswith("ws_run failed: TimeoutError")
    assert "stopped" in result
    assert time.monotonic() - started < 30
    time.sleep(3)  # past the moment the command would have finished
    assert not late.exists(), "the command is no longer running"


# @ac AC-HARNESS-008.5
def test_ac_harness_008_5_the_limit_is_600_seconds():
    assert workspaces.RUN_TIMEOUT == 600
