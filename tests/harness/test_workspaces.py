"""Workspaces: the main checkout the phase peers share, a git worktree for `test`, chatinho's /ws, and /merge (REQ-HARNESS-006, REQ-HARNESS-007)."""

import asyncio
from pathlib import Path

from chatinho import LOCAL, ReplyStatus

from harness.scripted import BRANCH, ScriptedModel, User, call, chat, commit_all, git_out, head, new_change, peer_id, settle
from specworks.harness import build_harness
from specworks.harness.backend import GitBackend
from specworks.harness.workspaces import MergeCommand, SpecworksWorktrees

TEST_BRANCH = "peer/test"


def worktrees(root):
    """The worktree folders git knows, the main checkout first, by branch (None for a detached one)."""
    found, folder = {}, None
    for line in git_out(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            folder = Path(line.removeprefix("worktree ")).resolve()
            found[folder] = None
        elif line.startswith("branch refs/heads/") and folder is not None:
            found[folder] = line.removeprefix("branch refs/heads/")
    return found


def worktree_of(root, branch=TEST_BRANCH):
    """The folder of the worktree on ``branch``, or None."""
    return next((folder for folder, on in worktrees(root).items() if on == branch), None)


def branches(root):
    return git_out(root, "branch", "--format=%(refname:short)").split()


def clean(root):
    return git_out(root, "status", "--porcelain", "--untracked-files=all").strip() == ""


def ask(name, text):
    async def then(session, user):
        await user.say(text, to=peer_id(session, name))

    return then


async def provision_test(ws):
    """`test`'s worktree, made by a provider of its own (as an earlier run would have), and its folder."""
    view = await SpecworksWorktrees(ws).provision("test", "test")
    return view.tree.root


def committed_test_file(ws, root):
    """`test`'s worktree with `tests/test_x.py` committed in it; its folder."""
    path = asyncio.run(provision_test(ws))
    (path / "tests").mkdir(exist_ok=True)
    (path / "tests/test_x.py").write_text("def test_x():\n    assert True\n", encoding="utf-8")
    commit_all(path, "tests")
    return path


# --- REQ-HARNESS-006 -------------------------------------------------------------


# @ac AC-HARNESS-006.1
def test_ac_harness_006_1_the_test_worktree(project, ws):
    start = head(project)
    model = ScriptedModel(script={"test": [call("write_file", file_path="/tests/test_x.py", content="x = 1\n"), "done"]})
    chat(ws, model, then=ask("test", "write the tests"))
    folder = worktree_of(project)
    assert folder is not None, "a worktree on peer/test"
    assert folder != project.resolve()
    assert (folder / "tests/test_x.py").read_text(encoding="utf-8") == "x = 1\n"
    assert head(folder) == start, f"started at {BRANCH}'s commit"
    assert not (project / "tests/test_x.py").exists()
    assert clean(project)


# @ac AC-HARNESS-006.2
def test_ac_harness_006_2_the_phase_peers_share_the_checkout(project, ws):
    model = ScriptedModel(
        script={
            "refine": [call("write_file", file_path="/notes.md", content="shared note\n"), "written"],
            "specify": [call("read_file", file_path="/notes.md"), "read"],
        }
    )

    async def then(session, user):
        await ask("refine", "write the notes")(session, user)
        await settle()  # refine has written before specify reads
        await ask("specify", "read the notes")(session, user)

    chat(ws, model, then=then)
    assert (project / "notes.md").read_text(encoding="utf-8") == "shared note\n"
    assert any("shared note" in result for result in model.runs_of("specify")[-1].tool_results())
    assert worktree_of(project) is None, "no worktree for a phase peer"


# @ac AC-HARNESS-006.2
def test_ac_harness_006_2_the_checkout_for_every_phase_peer(project, ws):
    async def main():
        provider = SpecworksWorktrees(ws)
        refine = await provider.provision("refine", "refine")
        specify = await provider.provision("specify", "specify")
        assert refine.tree.root == specify.tree.root == project.resolve()
        await refine.write("a.txt", "a\n")
        assert (await specify.read("a.txt")).text == "a\n"
        # another peer's view of the checkout reads it and cannot write it
        seen = await provider.provision("test", "refine")
        assert seen.tree.root == project.resolve()
        assert not hasattr(seen, "write")

    asyncio.run(main())


# @ac AC-HARNESS-006.3
def test_ac_harness_006_3_the_base_follows_the_checkout(project, ws):
    git_out(project, "checkout", "-q", "main")
    git_out(project, "branch", "-q", "-D", BRANCH)
    on_main = head(project)

    async def main():
        provider = SpecworksWorktrees(ws)
        await provider.initialize()  # the run starts on main
        git_out(project, "checkout", "-q", "-b", BRANCH)
        (project / "x.txt").write_text("x\n", encoding="utf-8")
        commit_all(project, "x")
        assert await provider.current_branch() == BRANCH
        view = await provider.provision("test", "test")
        return view.tree.root

    folder = asyncio.run(main())
    assert head(folder) == head(project) != on_main
    assert (folder / "x.txt").is_file()
    assert worktree_of(project) == folder.resolve()


# @ac AC-HARNESS-006.4
def test_ac_harness_006_4_reused(project, ws):
    first = asyncio.run(provision_test(ws))
    (first / "a.txt").write_text("a\n", encoding="utf-8")
    commit_all(first, "in the workspace")
    made = head(first)
    (project / "b.txt").write_text("b\n", encoding="utf-8")
    commit_all(project, "the checkout moves on")
    again = asyncio.run(provision_test(ws))  # a new run: a new provider
    assert again == first
    assert head(again) == made
    assert len([b for b in worktrees(project).values() if b == TEST_BRANCH]) == 1


# @ac AC-HARNESS-006.5
def test_ac_harness_006_5_listed(project, ws):
    path = asyncio.run(provision_test(ws))
    (path / "a.txt").write_text("a\n", encoding="utf-8")
    commit_all(path, "one commit")

    async def main():
        session = build_harness(ws, ScriptedModel(), frontend=User())
        return await session.commands["ws"].execute("", by=LOCAL)

    reply = asyncio.run(main())
    assert reply.status is not ReplyStatus.ERROR
    assert "test" in reply.text and TEST_BRANCH in reply.text
    assert "1 commit ahead" in reply.text


# --- REQ-HARNESS-007 -------------------------------------------------------------


def merge(ws, module, change, name, by=LOCAL):
    async def main():
        backend = GitBackend(ws, module)
        backend.change = change  # the run's change, as if a peer had worked on it
        return await MergeCommand(SpecworksWorktrees(ws), backend).execute(name, by=by)

    return asyncio.run(main())


# @ac AC-HARNESS-007.1
def test_ac_harness_007_1_merged(project, ws, module):
    change = new_change(project)
    path = committed_test_file(ws, project)
    reply = merge(ws, module, change, "test")
    assert reply.status is not ReplyStatus.ERROR
    assert "merged" in reply.text.lower()
    assert (project / "tests/test_x.py").read_text(encoding="utf-8") == "def test_x():\n    assert True\n"
    assert not path.exists()
    assert worktree_of(project) is None
    assert TEST_BRANCH not in branches(project)


# @ac AC-HARNESS-007.1
def test_ac_harness_007_1_merged_from_the_session(project, ws, module):
    change = new_change(project)
    committed_test_file(ws, project)

    async def main():
        session = build_harness(ws, ScriptedModel(), frontend=User())
        session.backend.change = change  # the run's change, as if a peer had worked on it
        return await session.commands["merge"].execute("test", by=LOCAL)

    reply = asyncio.run(main())
    assert reply.status is not ReplyStatus.ERROR and "merged" in reply.text.lower()
    assert (project / "tests/test_x.py").is_file()
    assert TEST_BRANCH not in branches(project)


# @ac AC-HARNESS-007.2
def test_ac_harness_007_2_a_conflict(project, ws, module):
    (project / "src").mkdir(exist_ok=True)
    (project / "src/a.py").write_text("a = 0\n", encoding="utf-8")
    commit_all(project, "a")
    change = new_change(project)
    path = asyncio.run(provision_test(ws))
    (path / "src/a.py").write_text("a = 2\n", encoding="utf-8")
    commit_all(path, "theirs")
    (project / "src/a.py").write_text("a = 1\n", encoding="utf-8")
    commit_all(project, "ours")
    before = head(project)
    reply = merge(ws, module, change, "test")
    assert reply.status is ReplyStatus.ERROR
    assert "src/a.py" in reply.text
    assert head(project) == before
    assert not (project / ".git/MERGE_HEAD").exists()
    assert clean(project)
    assert (project / "src/a.py").read_text(encoding="utf-8") == "a = 1\n"
    assert path.is_dir() and (path / "src/a.py").read_text(encoding="utf-8") == "a = 2\n"
    assert TEST_BRANCH in branches(project)


# @ac AC-HARNESS-007.3
def test_ac_harness_007_3_unknown(project, ws, module):
    change = new_change(project)
    before = (head(project), branches(project))
    reply = merge(ws, module, change, "nope")
    assert reply.status is ReplyStatus.ERROR
    assert "no workspace 'nope'" in reply.text
    assert (head(project), branches(project)) == before


# @ac AC-HARNESS-007.4
def test_ac_harness_007_4_a_model_cannot_merge(project, ws, module):
    new_change(project)
    path = committed_test_file(ws, project)
    made, before = head(path), head(project)
    model = ScriptedModel(script={"build": [call("run_merge", arguments="test"), "done"]})
    chat(ws, model, then=ask("build", "build add-x"))
    [result] = model.runs_of("build")[-1].tool_results()
    assert "only the user can merge" in result
    assert head(project) == before and not (project / "tests/test_x.py").exists()
    assert path.is_dir() and head(path) == made
    assert TEST_BRANCH in branches(project)


# @ac AC-HARNESS-007.4
def test_ac_harness_007_4_refused_for_any_peer(project, ws, module):
    change = new_change(project)
    path = committed_test_file(ws, project)
    before = head(project)
    reply = merge(ws, module, change, "test", by=3)
    assert reply.status is ReplyStatus.ERROR
    assert "only the user can merge" in reply.text
    assert head(project) == before and path.is_dir()


# @ac AC-HARNESS-007.5
def test_ac_harness_007_5_no_change_yet(project, ws, module):
    path = committed_test_file(ws, project)
    before = head(project)
    reply = merge(ws, module, None, "test")
    assert reply.status is ReplyStatus.ERROR
    assert "the run has no change yet: ask the peer working on the change to go on with it (such as @build go on with <change>), then merge" in reply.text
    assert "create" not in reply.text
    assert head(project) == before and not (project / "tests/test_x.py").exists()
    assert path.is_dir() and TEST_BRANCH in branches(project)
