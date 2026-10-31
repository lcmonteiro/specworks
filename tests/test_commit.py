"""Committing a phase: the files dirty when the phase started, and `specworks commit`, which commits only the phase's own."""

import hashlib
import json

import pytest
import yaml
from typer.testing import CliRunner

from helpers import git, init_repo, on_a_branch
from specworks.cli import app
from specworks.core.changes import META_FILE, commit_phase, load_change, set_phase
from specworks.core.config import load_config
from specworks.core.git import GitError, git_text

runner = CliRunner()
REF = "add-login"
CHANGE = f".specworks/changes/active/{REF}"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        pytest.fail(result.output)


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A project with the change `add-login` and `notes.txt`, `old.txt` and `src/a.py`, all committed on main; work goes on on `feature`."""
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    assert run_json("new", REF, "--no-branch")[0] == 0
    (tmp_path / "notes.txt").write_bytes(b"notes\n")
    (tmp_path / "old.txt").write_bytes(b"old\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.py").write_bytes(b"A = 1\n")
    on_a_branch(tmp_path, monkeypatch)
    return tmp_path


def change(root):
    return load_change(load_config(root), REF)


def meta(root):
    return yaml.safe_load((root / CHANGE / META_FILE).read_text(encoding="utf-8"))


def record(root, **files):
    """Save the change's record as if the phase had started with exactly these files dirty (path -> content)."""
    ch = change(root)
    ch.dirty = {path.replace("__", "/"): sha(content) for path, content in files.items()}
    ch.save()
    git(root, "add", "--", f"{CHANGE}/{META_FILE}")
    git(root, "commit", "-q", "--allow-empty", "-m", "record")  # the change folder starts clean
    return change(root)


def head(root):
    return git_text(root, "rev-parse", "HEAD").strip()


def message(root):
    return git_text(root, "log", "-1", "--format=%B").strip()


def files_in_head(root):
    return set(git_text(root, "show", "--name-only", "--format=", "HEAD").split())


def dirty_now(root):
    return set(git_text(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines())


def staged(root):
    return git_text(root, "diff", "--cached", "--name-only").split()


# @ac AC-PROJ-023.1
def test_a_phase_move_records_the_modified_untracked_and_deleted_files(project):
    (project / "notes.txt").write_bytes(b"notes, edited\n")
    (project / "draft.md").write_bytes(b"# draft\n")
    (project / "old.txt").unlink()
    ch = change(project)
    set_phase(ch, "specify")  # no root: nothing recorded
    assert change(project).dirty == {}
    set_phase(ch, "design", project)
    expected = {"notes.txt": sha(b"notes, edited\n"), "draft.md": sha(b"# draft\n"), "old.txt": "deleted"}
    for dirty in (change(project).dirty, meta(project)["dirty"]):
        assert {path: dirty.get(path) for path in expected} == expected
    assert "src/a.py" not in change(project).dirty  # clean files are not recorded


# @ac AC-PROJ-023.1
def test_the_phase_command_records_paths_relative_to_the_workspace_root(project):
    (project / "src/a.py").write_bytes(b"A = 2\n")
    code, _ = run_json("phase", "design", "--change", REF)
    assert code == 0
    assert change(project).dirty.get("src/a.py") == sha(b"A = 2\n")


# @ac AC-PROJ-023.2
def test_moving_to_the_phase_the_change_is_in_keeps_its_record(project):
    ch = change(project)
    set_phase(ch, "design")
    (project / "notes.txt").write_bytes(b"notes, edited\n")
    set_phase(ch, "implement", project)
    before = change(project).dirty
    assert "notes.txt" in before and "src/a.py" not in before
    (project / "src/a.py").write_bytes(b"A = 2\n")
    set_phase(change(project), "implement", project)
    assert change(project).dirty == before
    assert "src/a.py" not in meta(project).get("dirty", {})


# @ac AC-PROJ-023.3
def test_a_change_with_no_record_loads_with_no_recorded_files(project):
    path = project / CHANGE / META_FILE
    path.write_text(f"name: {REF}\ncreated: '2026-01-01T00:00:00'\nphase: design\n", encoding="utf-8")
    ch = change(project)
    assert ch.phase == "design" and ch.dirty == {}
    ch.save()
    assert "dirty" not in meta(project)  # an empty record is not written


# @ac AC-PROJ-024.1
def test_a_phase_commit_holds_only_the_files_changed_since_the_phase_started(project):
    (project / "notes.txt").write_bytes(b"notes, before the phase\n")
    ch = record(project, **{"notes.txt": b"notes, before the phase\n"})
    (project / "src/a.py").write_bytes(b"A = 2\n")
    (project / "tests").mkdir()
    (project / "tests/test_a.py").write_bytes(b"def test_a(): ...\n")
    (project / CHANGE / "tasks.md").write_bytes(b"# Tasks\n")
    result = commit_phase(project, REF, ch)
    phase_files = {"src/a.py", "tests/test_a.py", f"{CHANGE}/tasks.md"}
    assert result.commit is not None and head(project).startswith(result.commit)
    assert phase_files <= set(result.committed) and "notes.txt" not in result.committed
    assert phase_files <= files_in_head(project) and "notes.txt" not in files_in_head(project)
    assert result.left_out == ["notes.txt"] and result.already_dirty == []
    assert dirty_now(project) == {" M notes.txt"}  # still dirty, and nothing else is


# @ac AC-PROJ-024.2
def test_a_file_dirty_before_the_phase_and_changed_again_is_committed_and_flagged(project):
    (project / "notes.txt").write_bytes(b"notes, before the phase\n")
    ch = record(project, **{"notes.txt": b"notes, before the phase\n"})
    (project / "notes.txt").write_bytes(b"notes, during the phase\n")
    result = commit_phase(project, REF, ch)
    assert "notes.txt" in result.committed and "notes.txt" in files_in_head(project)
    assert result.already_dirty == ["notes.txt"] and result.left_out == []
    assert dirty_now(project) == set()


# @ac AC-PROJ-024.3
def test_the_message_is_the_ref_and_phase_then_the_trailers_in_order(project):
    set_phase(change(project), "design")
    ch = record(project)
    (project / "src/a.py").write_bytes(b"A = 2\n")
    result = commit_phase(project, REF, ch, trailers=["Co-Authored-By: A <a@x>", "Session: s1"])
    assert result.subject == "add-login: design"
    assert message(project) == "add-login: design\n\nCo-Authored-By: A <a@x>\nSession: s1"


# @ac AC-PROJ-024.3
def test_a_given_subject_replaces_the_ref_and_phase(project):
    set_phase(change(project), "design")
    ch = record(project)
    (project / "src/a.py").write_bytes(b"A = 2\n")
    result = commit_phase(project, REF, ch, subject="Add the login form", trailers=["Session: s1"])
    assert result.subject == "Add the login form"
    assert message(project) == "Add the login form\n\nSession: s1"


# @ac AC-PROJ-024.4
def test_nothing_changed_since_the_record_creates_no_commit(project):
    (project / "notes.txt").write_bytes(b"notes, before the phase\n")
    ch = record(project, **{"notes.txt": b"notes, before the phase\n"})
    before = head(project)
    result = commit_phase(project, REF, ch)
    assert result.commit is None and result.committed == []
    assert result.left_out == ["notes.txt"]
    assert head(project) == before and staged(project) == []


# @ac AC-PROJ-024.4, AC-CLI-012.2
def test_the_command_says_there_is_nothing_to_commit(project):
    record(project)
    result = runner.invoke(app, ["commit", "--change", REF])
    assert result.exit_code == 0, result.output
    assert f"nothing to commit for {REF}: no file changed since the phase started" in result.output


# @ac AC-PROJ-024.5
def test_a_detached_head_is_refused_before_staging_anything(project):
    ch = record(project)
    git(project, "checkout", "-q", "--detach")
    before = head(project)
    (project / "src/a.py").write_bytes(b"A = 2\n")
    (project / "draft.md").write_bytes(b"# draft\n")
    with pytest.raises(GitError) as error:
        commit_phase(project, REF, ch)
    assert "cannot commit on a detached HEAD; switch to a branch first" in str(error.value)
    assert staged(project) == [] and head(project) == before


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
