"""Committing a phase: the files dirty when the phase started, and `specworks commit`, which commits only the phase's own."""

import pytest

from helpers import REF as CLOSED_REF
from specworks.cli import app
from specworks.core.changes import META_FILE
from specworks.core.git import git_text
from support.commit import CHANGE, REF, head, make_closed, make_project, message, record, run_json, runner


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


# @ac AC-CLI-012.1
def test_the_command_commits_with_the_trailers_and_returns_relative_paths(project):
    (project / "notes.txt").write_bytes(b"notes, before the phase\n")
    assert run_json("phase", "design", "--change", REF)[0] == 0  # records notes.txt
    (project / "src/a.py").write_bytes(b"A = 2\n")
    code, data = run_json("commit", "--change", REF, "--trailer", "Co-Authored-By: A <a@x>")
    assert code == 0, data
    assert data["ref"] == REF and data["subject"] == "add-login: design"
    assert isinstance(data["commit"], str) and head(project).startswith(data["commit"])
    assert "src/a.py" in data["committed"] and f"{CHANGE}/{META_FILE}" in data["committed"]
    assert data["leftOut"] == ["notes.txt"] and data["alreadyDirty"] == []
    for path in [*data["committed"], *data["leftOut"]]:
        assert not path.startswith("/") and str(project) not in path and "\\" not in path
    assert message(project) == "add-login: design\n\nCo-Authored-By: A <a@x>"


# @ac AC-CLI-012.1
def test_the_command_prints_the_commit_and_the_files_left_out(project):
    (project / "notes.txt").write_bytes(b"notes, before the phase\n")
    assert run_json("phase", "design", "--change", REF)[0] == 0
    (project / "src/a.py").write_bytes(b"A = 2\n")
    result = runner.invoke(app, ["commit", "--change", REF, "--message", "Add the login form"])
    assert result.exit_code == 0, result.output
    short = git_text(project, "rev-parse", "--short", "HEAD").strip()
    assert f"{short} Add the login form" in result.output
    assert "src/a.py" in result.output
    assert "left out (unchanged since the phase started): notes.txt" in result.output
    assert message(project) == "Add the login form"


# @ac AC-CLI-012.1, AC-PROJ-024.2
def test_the_command_prints_the_files_already_dirty(project):
    (project / "notes.txt").write_bytes(b"notes, before the phase\n")
    assert run_json("phase", "design", "--change", REF)[0] == 0
    (project / "notes.txt").write_bytes(b"notes, during the phase\n")
    result = runner.invoke(app, ["commit", "--change", REF])
    assert result.exit_code == 0, result.output
    assert "already dirty when the phase started: notes.txt" in result.output


# @ac AC-CLI-012.2
def test_the_command_returns_a_null_commit_when_nothing_changed(project):
    record(project)
    before = head(project)
    code, data = run_json("commit", "--change", REF)
    assert code == 0, data
    assert data["commit"] is None and data["committed"] == []
    assert head(project) == before


# @ac AC-CLI-012.3
def test_the_command_refuses_an_unknown_change_naming_it(project):
    code, data = run_json("commit", "--change", "nope")
    assert code == 1 and "nope" in data["error"]


@pytest.fixture
def closed(tmp_path, monkeypatch):
    return make_closed(tmp_path, monkeypatch)


# @ac AC-CLI-012.3
def test_the_command_refuses_a_ref_neither_active_nor_archived(closed):
    root, _ = closed
    before = head(root)
    code, data = run_json("commit", "--change", "nope")
    assert code == 1 and "nope" in data["error"]
    assert head(root) == before


# @ac AC-CLI-012.4
def test_the_command_commits_a_change_that_close_has_just_archived(closed):
    root, archived_to = closed
    code, data = run_json("commit", "--change", CLOSED_REF)
    assert code == 0, data
    assert data["ref"] == CLOSED_REF and data["subject"] == f"{CLOSED_REF}: close"
    assert isinstance(data["commit"], str) and head(root).startswith(data["commit"])
    assert f"{archived_to}/{META_FILE}" in data["committed"]
    assert f".specworks/changes/active/{CLOSED_REF}/{META_FILE}" in data["committed"]
    assert data["alreadyDirty"] == []  # dirty when close started, but the change's own
    for path in [*data["committed"], *data["leftOut"]]:
        assert not path.startswith("/") and str(root) not in path and "\\" not in path
    assert message(root) == f"{CLOSED_REF}: close"
