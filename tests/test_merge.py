"""Merging a half's branch: `specworks merge <branch>` resolves the change's tasks.md and traceability.md, aborts on anything else."""

import pytest

from helpers import REF, git, remove_repo, run_json
from specworks.cli.output import resolve_change
from specworks.core.git import git_text
from specworks.core.workspace import load_workspace
from specworks.specs.trace import Analysis, to_markdown
from specworks.workflow.merge import BranchMergeError, merge_branch, merge_ticks

CHANGE = f".specworks/changes/active/{REF}"
TASKS_MD = f"{CHANGE}/tasks.md"
TRACE_MD = f"{CHANGE}/traceability.md"
BRANCH = "half"


@pytest.fixture
def halves(project, monkeypatch):
    """The planned project committed on main, with the change's trace written, and a `half` branch from there; on main."""
    for key, value in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(key, value)
    (project / "src/auth/session.py").write_text("def session():\n    return 1\n")
    run_json("trace", "--change", REF, "--write")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "baseline")
    git(project, "branch", BRANCH)
    return project


def commit_on(root, branch, files, message):
    """Check out `branch`, write `files` ({relative path: text}), commit them."""
    git(root, "checkout", "-q", branch)
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)


def tick(root, *numbers):
    """tasks.md with the given tasks ticked."""
    text = (root / TASKS_MD).read_text(encoding="utf-8")
    for n in numbers:
        text = text.replace(f"- [ ] {n} ", f"- [x] {n} ")
    return text


def head(root):
    return git_text(root, "rev-parse", "HEAD").strip()


def parents(root):
    return git_text(root, "rev-list", "--parents", "-n", "1", "HEAD").split()[1:]


def status(root):
    return git_text(root, "status", "--porcelain").strip()


def merging(root):
    return (root / ".git/MERGE_HEAD").exists()


def merge(root, branch=BRANCH):
    ws = load_workspace(root)
    mod, ch = resolve_change(ws, REF)
    return ws, merge_branch(ws, mod, ch, branch)


def snapshot(root):
    """HEAD and the text of every file git knows, to check an aborted merge left the checkout as it was."""
    files = git_text(root, "ls-files").split()
    return head(root), {f: (root / f).read_text(encoding="utf-8") for f in files}


# @ac AC-FLOW-015.1
def test_ac_flow_015_1_no_conflict_merges_and_resolves_nothing(halves):
    commit_on(halves, BRANCH, {"tests/test_reset.py": "# @ac AC-AUTH-003.1\ndef test_reset():\n    assert False\n"}, "tests")  # specworks: ignore-tags
    commit_on(halves, "main", {"src/auth/reset.py": "def reset(): ...\n"}, "code")
    ws, result = merge(halves)
    assert result.merged is True and result.branch == BRANCH and result.resolved == []
    assert len(parents(halves)) == 2 and status(halves) == "" and not merging(halves)
    assert (halves / "tests/test_reset.py").is_file() and (halves / "src/auth/reset.py").is_file()


# @ac AC-FLOW-015.2
def test_ac_flow_015_2_ticks_on_both_sides_are_all_kept(halves):
    commit_on(halves, BRANCH, {TASKS_MD: tick(halves, "1.1")}, "test half")
    commit_on(halves, "main", {TASKS_MD: tick(halves, "1.2")}, "code half")
    ws, result = merge(halves)
    assert result.merged is True and [ws.rel(p) for p in result.resolved] == [TASKS_MD]
    text = (halves / TASKS_MD).read_text(encoding="utf-8")
    assert "- [x] 1.1 [test]" in text and "- [x] 1.2 [code]" in text and "- [x] 2.1 [code]" in text
    assert "<<<<<<<" not in text and text.count("1.1 [test]") == 1
    assert len(parents(halves)) == 2 and status(halves) == "" and not merging(halves)


# @ac AC-FLOW-015.3
def test_ac_flow_015_3_the_trace_is_regenerated_from_the_merged_checkout(halves):
    test_file = "# @ac AC-AUTH-003.1\ndef test_reset():\n    assert False\n"  # specworks: ignore-tags
    commit_on(halves, BRANCH, {"tests/test_reset.py": test_file, TRACE_MD: "# Traceability: the test half's\n"}, "test half")
    commit_on(halves, "main", {"src/auth/reset.py": "# @req REQ-AUTH-003\ndef reset(): ...\n", TRACE_MD: "# Traceability: the code half's\n"}, "code half")  # specworks: ignore-tags
    ws, result = merge(halves)
    assert result.merged is True and [ws.rel(p) for p in result.resolved] == [TRACE_MD]
    assert len(parents(halves)) == 2 and status(halves) == "" and not merging(halves)
    ws = load_workspace(halves)
    mod, ch = resolve_change(ws, REF)
    analysis = Analysis(ws, ch)
    expected = to_markdown(mod.qualify(ch.name), analysis.rows, analysis.gaps)
    text = (halves / TRACE_MD).read_text(encoding="utf-8")
    assert text == expected
    assert "tests/test_reset.py" in text and "src/auth/reset.py" in text


# @ac AC-FLOW-015.2, AC-FLOW-015.3
def test_both_files_conflicting_are_both_resolved(halves):
    commit_on(halves, BRANCH, {TASKS_MD: tick(halves, "1.1"), TRACE_MD: "theirs\n"}, "test half")
    commit_on(halves, "main", {TASKS_MD: tick(halves, "1.2"), TRACE_MD: "ours\n"}, "code half")
    ws, result = merge(halves)
    assert result.merged is True and sorted(ws.rel(p) for p in result.resolved) == sorted([TASKS_MD, TRACE_MD])
    assert len(parents(halves)) == 2 and status(halves) == ""


# @ac AC-FLOW-015.4
def test_ac_flow_015_4_another_conflicting_file_aborts_the_merge(halves):
    commit_on(halves, BRANCH, {"src/auth/session.py": "def session():\n    return 2\n", TASKS_MD: tick(halves, "1.1")}, "test half")
    commit_on(halves, "main", {"src/auth/session.py": "def session():\n    return 3\n", TASKS_MD: tick(halves, "1.2")}, "code half")
    before = snapshot(halves)
    with pytest.raises(BranchMergeError) as exc:
        merge(halves)
    assert "session.py" in str(exc.value)
    assert [p.name for p in exc.value.files if p.name != "tasks.md"] == ["session.py"]
    assert snapshot(halves) == before and status(halves) == "" and not merging(halves)


# @ac AC-FLOW-015.5
def test_ac_flow_015_5_a_task_whose_text_differs_aborts_the_merge(halves):
    theirs = tick(halves, "1.1").replace("Write failing tests", "Write the failing tests")
    commit_on(halves, BRANCH, {TASKS_MD: theirs}, "test half")
    commit_on(halves, "main", {TASKS_MD: tick(halves, "1.2")}, "code half")
    before = snapshot(halves)
    with pytest.raises(BranchMergeError) as exc:
        merge(halves)
    assert "tasks.md" in str(exc.value) and [p.name for p in exc.value.files] == ["tasks.md"]
    assert snapshot(halves) == before and status(halves) == "" and not merging(halves)


# @ac AC-FLOW-015.6
def test_ac_flow_015_6_uncommitted_changes_are_refused_before_merging(halves):
    commit_on(halves, BRANCH, {"tests/test_reset.py": "def test_x():\n    pass\n"}, "test half")
    git(halves, "checkout", "-q", "main")
    (halves / "src/auth/session.py").write_text("def session():\n    return 9\n")
    before = head(halves)
    with pytest.raises(BranchMergeError) as exc:
        merge(halves)
    assert "uncommitted" in str(exc.value).lower() and exc.value.files == []
    assert head(halves) == before and not merging(halves) and not (halves / "tests/test_reset.py").exists()
    assert (halves / "src/auth/session.py").read_text() == "def session():\n    return 9\n"


# @ac AC-FLOW-015.6
def test_ac_flow_015_6_an_unknown_branch_is_refused_before_merging(halves):
    before = snapshot(halves)
    with pytest.raises(BranchMergeError) as exc:
        merge(halves, "no-such-branch")
    assert "no-such-branch" in str(exc.value) and exc.value.files == []
    assert snapshot(halves) == before and status(halves) == "" and not merging(halves)


# @ac AC-FLOW-015.2
def test_merge_ticks_keeps_a_tick_from_either_side():
    ours = "# Tasks\n\n- [x] 1.1 [test] a\n- [ ] 1.2 [code] b\n- [ ] 1.3 [code] c\n"
    theirs = "# Tasks\n\n- [ ] 1.1 [test] a\n- [x] 1.2 [code] b\n- [ ] 1.3 [code] c\n"
    assert merge_ticks(ours, theirs) == "# Tasks\n\n- [x] 1.1 [test] a\n- [x] 1.2 [code] b\n- [ ] 1.3 [code] c\n"


# @ac AC-FLOW-015.2
def test_merge_ticks_keeps_our_line_endings():
    ours = "# Tasks\r\n\r\n- [ ] 1.1 a\r\n- [x] 1.2 b\r\n"
    theirs = "# Tasks\n\n- [x] 1.1 a\n- [ ] 1.2 b\n"
    assert merge_ticks(ours, theirs) == "# Tasks\r\n\r\n- [x] 1.1 a\r\n- [x] 1.2 b\r\n"


# @ac AC-FLOW-015.5
@pytest.mark.parametrize(
    "theirs",
    [
        "# Tasks\n\n- [x] 1.1 [test] a, changed\n- [ ] 1.2 [code] b\n",
        "# Tasks\n\n- [x] 1.1 [test] a\n- [ ] 1.2 [code] b\n- [ ] 1.3 [code] new\n",
        "# Tasks\n\n- [x] 1.1 [test] a\n",
    ],
    ids=["text", "added line", "removed line"],
)
def test_merge_ticks_refuses_lines_that_differ_in_more_than_their_box(theirs):
    assert merge_ticks("# Tasks\n\n- [ ] 1.1 [test] a\n- [x] 1.2 [code] b\n", theirs) is None


# @ac AC-CLI-010.1
def test_ac_cli_010_1_merge_prints_the_resolved_files_relative_to_the_root(halves):
    commit_on(halves, BRANCH, {TASKS_MD: tick(halves, "1.1")}, "test half")
    commit_on(halves, "main", {TASKS_MD: tick(halves, "1.2")}, "code half")
    code, data = run_json("merge", BRANCH, "--change", REF)
    assert code == 0, data
    assert data["merged"] is True and data["branch"] == BRANCH and data["resolved"] == [TASKS_MD]
    assert status(halves) == "" and not merging(halves)


# @ac AC-CLI-010.2
def test_ac_cli_010_2_an_aborted_merge_is_an_error_naming_the_files(halves):
    commit_on(halves, BRANCH, {"src/auth/session.py": "def session():\n    return 2\n"}, "test half")
    commit_on(halves, "main", {"src/auth/session.py": "def session():\n    return 3\n"}, "code half")
    before = snapshot(halves)
    code, data = run_json("merge", BRANCH, "--change", REF)
    assert code == 1 and "src/auth/session.py" in data["error"]
    assert snapshot(halves) == before and not merging(halves)


# @ac AC-CLI-010.3
def test_ac_cli_010_3_outside_git_is_refused(halves):
    remove_repo(halves)
    tasks = (halves / TASKS_MD).read_text(encoding="utf-8")
    code, data = run_json("merge", BRANCH, "--change", REF)
    assert code == 1 and "git repository" in data["error"]
    assert (halves / TASKS_MD).read_text(encoding="utf-8") == tasks and not (halves / ".git").exists()
