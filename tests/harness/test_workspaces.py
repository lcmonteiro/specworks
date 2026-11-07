"""Workspaces: git worktrees peers work in, opened with /workspace and merged with /merge (REQ-HARNESS-006, REQ-HARNESS-007)."""

import asyncio
from pathlib import Path

import pytest
from chatinho import ReplyStatus

from harness.scripted import BRANCH, ScriptedModel, call, chat, commit_all, git_out, head, new_change, peer_id
from specworks.harness.backend import GitBackend
from specworks.harness.workspaces import WORKSPACES_DIR, MergeCommand, WorkspaceCommand, WorkspaceError, Workspaces

TEST, CODE = 1, 2  # two peer ids


def worktrees(root):
    """The worktree folders git knows, the main checkout first."""
    return [line.removeprefix("worktree ") for line in git_out(root, "worktree", "list", "--porcelain").splitlines() if line.startswith("worktree ")]


def branches(root):
    return git_out(root, "branch", "--format=%(refname:short)").split()


def run(coro):
    return asyncio.run(coro)


# --- /workspace (REQ-HARNESS-006) ----------------------------------------------


# @ac AC-HARNESS-006.1
def test_ac_harness_006_1_a_new_workspace(project, ws):
    start = head(project)
    model = ScriptedModel(script={"test": [call("run_workspace", arguments="test-half"), call("write_file", file_path="/tests/test_new.py", content="x = 1\n"), "done"]})

    async def ask_test(session, user):
        await user.say("write the tests", to=peer_id(session, "test"))

    chat(ws, model, then=ask_test)
    folder = project / WORKSPACES_DIR / "test-half"
    assert folder.is_dir() and folder.resolve() in [Path(p).resolve() for p in worktrees(project)]
    assert git_out(folder, "rev-parse", "--abbrev-ref", "HEAD").strip() == f"{BRANCH}--test-half"
    assert head(folder) == start
    assert git_out(project, "status", "--porcelain", "--untracked-files=all").strip() == ""
    assert (folder / "tests/test_new.py").read_text(encoding="utf-8") == "x = 1\n"
    assert not (project / "tests/test_new.py").exists()


# @ac AC-HARNESS-006.1
def test_ac_harness_006_1_opened_for_the_peer(project, ws, module):
    spaces = Workspaces(ws, module)
    assert spaces.name_of(TEST) == "main" and spaces.path_of(TEST) == ws.root
    path = spaces.open("test-half", TEST)
    assert path.resolve() == (project / WORKSPACES_DIR / "test-half").resolve()
    assert spaces.path_of(TEST) == path and spaces.name_of(TEST) == "test-half"
    assert spaces.branch_of("test-half") == f"{BRANCH}--test-half"
    assert spaces.path_of(CODE) == ws.root  # only the peer that opened it moves
    assert git_out(project, "status", "--porcelain", "--untracked-files=all").strip() == ""


# @ac AC-HARNESS-006.2
def test_ac_harness_006_2_reused(project, ws, module):
    spaces = Workspaces(ws, module)
    path = spaces.open("test-half", TEST)
    (path / "a.txt").write_text("a\n", encoding="utf-8")
    commit_all(path, "in the workspace")
    made = head(path)
    again = spaces.open("test-half", CODE)
    assert again == path
    assert head(again) == made
    assert spaces.name_of(CODE) == "test-half" and spaces.path_of(CODE) == path


# @ac AC-HARNESS-006.2
def test_ac_harness_006_2_reused_by_the_command(project, ws, module):
    spaces = Workspaces(ws, module)
    command = WorkspaceCommand(spaces)
    first = run(command.execute("test-half", by=TEST))
    assert first.status is ReplyStatus.ANSWERED
    second = run(command.execute("test-half", by=CODE))
    assert second.status is ReplyStatus.ANSWERED
    assert spaces.path_of(CODE) == spaces.path_of(TEST) != ws.root


# @ac AC-HARNESS-006.3
def test_ac_harness_006_3_back_to_main(project, ws, module):
    spaces = Workspaces(ws, module)
    spaces.open("test-half", TEST)
    assert spaces.open("main", TEST) == ws.root
    assert spaces.path_of(TEST) == ws.root and spaces.name_of(TEST) == "main"


# @ac AC-HARNESS-006.3
def test_ac_harness_006_3_file_tools_back_in_main(project, ws):
    model = ScriptedModel(
        script={
            "test": [
                call("run_workspace", arguments="test-half"),
                call("run_workspace", arguments="main"),
                call("write_file", file_path="/back.txt", content="main\n"),
                "done",
            ]
        }
    )

    async def ask_test(session, user):
        await user.say("go and come back", to=peer_id(session, "test"))

    chat(ws, model, then=ask_test)
    assert (project / "back.txt").read_text(encoding="utf-8") == "main\n"
    assert not (project / WORKSPACES_DIR / "test-half/back.txt").exists()


# @ac AC-HARNESS-006.4
@pytest.mark.parametrize("name", ["../x", "Test"])
def test_ac_harness_006_4_a_bad_name(project, ws, module, name):
    spaces = Workspaces(ws, module)
    before = (branches(project), worktrees(project))
    with pytest.raises(WorkspaceError) as error:
        spaces.open(name, TEST)
    assert "lowercase letters, digits and hyphens" in str(error.value)
    reply = run(WorkspaceCommand(spaces).execute(name, by=TEST))
    assert reply.status is ReplyStatus.ERROR and "lowercase letters, digits and hyphens" in reply.text
    assert (branches(project), worktrees(project)) == before
    assert spaces.path_of(TEST) == ws.root
    assert not (project / ".specworks/x").exists() and not (project / WORKSPACES_DIR / "Test").exists()


# --- /merge (REQ-HARNESS-007) --------------------------------------------------


def merge(ws, module, spaces, change, name):
    return run(MergeCommand(spaces, GitBackend(ws, module, change)).execute(name, by=CODE))


# @ac AC-HARNESS-007.1
def test_ac_harness_007_1_merged(project, ws, module):
    change = new_change(project)
    spaces = Workspaces(ws, module)
    path = spaces.open("test-half", TEST)
    (path / "tests").mkdir()
    (path / "tests/test_x.py").write_text("def test_x():\n    assert True\n", encoding="utf-8")
    commit_all(path, "tests")
    reply = merge(ws, module, spaces, change, "test-half")
    assert reply.status is ReplyStatus.ANSWERED and "merged" in reply.text.lower()
    assert (project / "tests/test_x.py").read_text(encoding="utf-8") == "def test_x():\n    assert True\n"
    assert not path.exists()
    assert f"{BRANCH}--test-half" not in branches(project)
    assert len(worktrees(project)) == 1
    assert spaces.path_of(TEST) == ws.root and spaces.name_of(TEST) == "main"


# @ac AC-HARNESS-007.2
def test_ac_harness_007_2_a_conflict(project, ws, module):
    (project / "src").mkdir(exist_ok=True)
    (project / "src/a.py").write_text("a = 0\n", encoding="utf-8")
    commit_all(project, "a")
    change = new_change(project)
    spaces = Workspaces(ws, module)
    path = spaces.open("test-half", TEST)
    (path / "src/a.py").write_text("a = 2\n", encoding="utf-8")
    commit_all(path, "theirs")
    (project / "src/a.py").write_text("a = 1\n", encoding="utf-8")
    commit_all(project, "ours")
    before = head(project)
    reply = merge(ws, module, spaces, change, "test-half")
    assert reply.status is ReplyStatus.ERROR and "src/a.py" in reply.text
    assert head(project) == before
    assert not (project / ".git/MERGE_HEAD").exists()
    assert git_out(project, "status", "--porcelain").strip() == ""
    assert (project / "src/a.py").read_text(encoding="utf-8") == "a = 1\n"
    assert path.is_dir() and (path / "src/a.py").read_text(encoding="utf-8") == "a = 2\n"
    assert f"{BRANCH}--test-half" in branches(project)
    with pytest.raises(WorkspaceError) as error:
        spaces.merge("test-half", change)
    assert [p.name for p in error.value.files] == ["a.py"]


# @ac AC-HARNESS-007.3
def test_ac_harness_007_3_unknown(project, ws, module):
    change = new_change(project)
    spaces = Workspaces(ws, module)
    reply = merge(ws, module, spaces, change, "nope")
    assert reply.status is ReplyStatus.ERROR and "no workspace 'nope'" in reply.text
    with pytest.raises(WorkspaceError) as error:
        spaces.merge("nope", change)
    assert "no workspace 'nope'" in str(error.value)
