"""`specworks reopen` (REQ-CLI-020) and `status` reading why a change was reopened (REQ-CLI-021)."""

import pytest
from typer.testing import CliRunner

from specworks.cli import app
from specworks.core.changes import archived_as
from specworks.core.config import load_config
from specworks.core.git import git_text
from support.close_phase import snapshot
from support.commit import CHANGE, REF, make_project, run_json
from support.reopen import DAY, commit_all, make_archived

runner = CliRunner()
OTHER = "add-other"


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


def reopen(*extra, ref=REF, reason="CI lint failed"):
    return run_json("reopen", "--change", ref, "--reason", reason, *extra)


def still_archived(root, ref=REF):
    return archived_as(load_config(root), ref) is not None and not (root / CHANGE).exists()


# @ac AC-CLI-020.1
def test_reopen_moves_the_change_to_active_in_review_and_says_so(project):
    make_archived(project, REF)
    code, data = reopen()
    assert code == 0, data
    assert data["path"] == CHANGE and data["phase"] == "review"
    assert [e["reason"] for e in data["reopened"]] == ["CI lint failed"]
    assert (project / CHANGE / "proposal.md").is_file()


# @ac AC-CLI-020.1
def test_the_text_output_names_the_path_and_the_phase(project):
    make_archived(project, REF)
    result = runner.invoke(app, ["reopen", "--change", REF, "--reason", "CI lint failed"])
    assert result.exit_code == 0, result.output
    assert CHANGE in result.output and "review" in result.output


# @ac AC-CLI-020.2
def test_reopen_can_start_in_refine(project):
    make_archived(project, REF)
    code, data = reopen("--phase", "refine")
    assert code == 0, data
    assert data["phase"] == "refine" and data["reopened"][-1]["phase"] == "refine"
    assert run_json("status", "--change", REF)[1]["phase"] == "refine"


# @ac AC-CLI-020.3
def test_reopen_needs_a_reason(project):
    make_archived(project, REF)
    result = runner.invoke(app, ["reopen", "--change", REF])
    assert result.exit_code != 0
    assert still_archived(project)


# @ac AC-CLI-020.3
def test_a_blank_reason_fails_and_the_change_stays_archived(project):
    make_archived(project, REF)
    before = snapshot(project)
    code, data = reopen(reason="  ")
    assert code == 1 and "reason" in data["error"]
    assert snapshot(project) == before and still_archived(project)


# @ac AC-CLI-020.4
def test_an_active_change_is_not_reopened(project):
    before = snapshot(project)
    code, data = reopen()
    assert code == 1 and "active" in data["error"]
    assert snapshot(project) == before


# @ac AC-CLI-020.4
def test_an_abandoned_change_is_not_reopened(project):
    make_archived(project, REF, abandoned="not needed")
    before = snapshot(project)
    code, data = reopen()
    assert code == 1 and "abandoned" in data["error"]
    assert snapshot(project) == before


# @ac AC-CLI-020.4
def test_an_unknown_change_is_not_found(project):
    before = snapshot(project)
    code, data = reopen(ref="no-such-change")
    assert code == 1 and "not found" in data["error"]
    assert snapshot(project) == before


# @ac AC-CLI-020.4
def test_a_closed_change_cannot_reopen_to_done(project):
    make_archived(project, REF)
    before = snapshot(project)
    code, data = reopen("--phase", "done")
    assert code == 1 and "specworks close" in data["error"]
    assert snapshot(project) == before and still_archived(project)


# @ac AC-CLI-020.5
def test_reopen_changes_no_branch_commit_or_living_doc(project):
    docs = project / "src/auth/docs"
    docs.mkdir(parents=True)
    (docs / "spec.md").write_text("# user-auth\n\n## Requirements\n", encoding="utf-8")
    (docs / "requirements.md").write_text("# Requirements: user-auth\n\n## History\n", encoding="utf-8")
    make_archived(project, REF)
    commit_all(project)
    branch, head = git_text(project, "rev-parse", "--abbrev-ref", "HEAD"), git_text(project, "rev-parse", "HEAD")
    living = {p: (docs / p).read_bytes() for p in ("spec.md", "requirements.md")}
    code, data = reopen()
    assert code == 0, data
    assert (git_text(project, "rev-parse", "--abbrev-ref", "HEAD"), git_text(project, "rev-parse", "HEAD")) == (branch, head)
    assert {p: (docs / p).read_bytes() for p in living} == living


# @ac AC-CLI-020.6
def test_commit_after_reopen_takes_the_active_folder_and_the_archive_removal(project):
    make_archived(project, REF)
    commit_all(project)
    assert reopen()[0] == 0
    code, data = run_json("commit", "--change", REF)
    assert code == 0, data
    assert data["alreadyDirty"] == []
    assert f"{CHANGE}/proposal.md" in data["committed"]
    assert f".specworks/changes/archive/{DAY}-{REF}/proposal.md" in data["committed"]
    assert git_text(project, "status", "--porcelain").strip() == ""


# @ac AC-CLI-021.1
def test_status_says_a_reopened_change_was_reopened_and_why(project):
    make_archived(project, REF)
    assert reopen()[0] == 0
    result = runner.invoke(app, ["status", "--change", REF])
    assert result.exit_code == 0 and "reopened" in result.output and "CI lint failed" in result.output
    code, data = run_json("status", "--change", REF)
    assert code == 0
    assert len(data["reopened"]) == 1
    entry = data["reopened"][0]
    assert entry["reason"] == "CI lint failed" and entry["phase"] == "review" and entry["at"]


# @ac AC-CLI-021.2
def test_a_change_never_reopened_has_no_reopened_key(project):
    code, data = run_json("status", "--change", REF)
    assert code == 0 and "reopened" not in data
    make_archived(project, OTHER)
    code, data = run_json("status", "--change", OTHER)
    assert code == 0 and "reopened" not in data


# @ac AC-CLI-002.7
def test_reopen_names_a_closed_change_by_name_or_by_archive_folder(project):
    make_archived(project, REF)
    make_archived(project, OTHER)
    code, data = reopen()
    assert code == 0, data
    code, data = reopen(ref=f"{DAY}-{OTHER}")
    assert code == 0, data
    assert data["path"] == f".specworks/changes/active/{OTHER}"
    assert archived_as(load_config(project), OTHER) is None
