"""Merging a half's branch: `specworks merge <branch>` resolves the change's tasks.md and traceability.md, aborts on anything else."""

import pytest

from helpers import REF, remove_repo, run_json
from support.merge import BRANCH, TASKS_MD, commit_on, make_halves, merging, snapshot, status, tick


@pytest.fixture
def halves(project, monkeypatch):
    return make_halves(project, monkeypatch)


# @ac AC-CLI-010.1
def test_ac_cli_010_1_merge_prints_the_resolved_files_relative_to_the_root(halves):
    commit_on(halves, BRANCH, {TASKS_MD: tick(halves, "1.1")}, "test half")
    commit_on(halves, "main", {TASKS_MD: tick(halves, "1.2")}, "code half")
    code, data = run_json("merge", BRANCH, "--change", REF)
    assert code == 0, data
    assert data["merged"] is True and data["branch"] == BRANCH and data["resolved"] == [TASKS_MD]
    text = (halves / TASKS_MD).read_text(encoding="utf-8")
    assert "- [x] 1.1 [test]" in text and "- [x] 1.2 [code]" in text
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
