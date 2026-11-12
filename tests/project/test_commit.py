"""
Committing a phase: the files dirty when the phase started, and `specworks commit`, which commits only the phase's own.
"""

import pytest
import yaml

from helpers import REF as CLOSED_REF
from helpers import git, init_repo, on_a_branch, remove_repo
from specworks.cli import app
from specworks.core.changes import META_FILE, archived_as, commit_phase, set_phase
from specworks.core.config import load_config
from specworks.core.git import GitError, git_text
from support.commit import CHANGE, REF, change, head, make_closed, make_project, message, record, run_json, runner, sha


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


def meta(root):
    return yaml.safe_load((root / CHANGE / META_FILE).read_text(encoding="utf-8"))


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
    before = change(project).dirty
    set_phase(ch, "specify")  # no root: the record is left as it was
    assert change(project).dirty == before
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


# @ac AC-PROJ-023.1
def test_a_workspace_below_the_git_root_records_only_its_own_files_relative_to_itself(tmp_path, monkeypatch):
    init_repo(tmp_path)
    workspace = tmp_path / "app"
    workspace.mkdir()
    monkeypatch.chdir(workspace)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    assert run_json("new", REF, "--no-branch")[0] == 0
    (workspace / "src").mkdir()
    (workspace / "src/a.py").write_bytes(b"A = 1\n")
    on_a_branch(tmp_path, monkeypatch)
    (tmp_path / "outside.txt").write_bytes(b"outside\n")
    (workspace / "src/a.py").write_bytes(b"A = 2\n")
    set_phase(change(workspace), "design", workspace)
    dirty = change(workspace).dirty
    assert dirty == {"src/a.py": sha(b"A = 2\n")}  # not `outside.txt`, and not `app/src/a.py`


# @ac AC-PROJ-023.1
def test_a_staged_rename_records_both_paths(project):
    git(project, "mv", "old.txt", "renamed.txt")
    set_phase(change(project), "design", project)
    dirty = change(project).dirty
    assert dirty.get("renamed.txt") == sha(b"old\n")
    assert dirty.get("old.txt") == "deleted"


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


# @ac AC-PROJ-023.4
def test_a_move_outside_a_git_repository_succeeds_with_no_record(project):
    remove_repo(project)
    ch = change(project)
    set_phase(ch, "specify")
    (project / "draft.md").write_bytes(b"# draft\n")
    set_phase(ch, "design", project)
    assert change(project).phase == "design" and change(project).dirty == {}
    assert "dirty" not in meta(project)


# @ac AC-PROJ-023.4
def test_the_phase_command_moves_a_change_outside_a_git_repository(project):
    remove_repo(project)
    code, data = run_json("phase", "design", "--change", REF)
    assert code == 0, data
    assert change(project).phase == "design" and change(project).dirty == {}


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


@pytest.fixture
def closed(tmp_path, monkeypatch):
    return make_closed(tmp_path, monkeypatch)


# @ac AC-PROJ-024.6
def test_a_closed_change_commits_its_archive_and_the_removal_of_its_active_folder(closed):
    root, archived_to = closed
    active = f".specworks/changes/active/{CLOSED_REF}"
    tracked_before = set(git_text(root, "ls-files", "--", active).split())
    assert f"{active}/{META_FILE}" in tracked_before
    ch = archived_as(load_config(root), CLOSED_REF)
    assert ch is not None and ch.phase == "done"
    result = commit_phase(root, CLOSED_REF, ch)
    assert result.subject == f"{CLOSED_REF}: close"
    assert result.commit is not None and head(root).startswith(result.commit)
    assert message(root) == f"{CLOSED_REF}: close"
    in_head = set(git_text(root, "show", "--name-only", "--no-renames", "--format=", "HEAD").split())  # a move shows both paths
    assert f"{archived_to}/{META_FILE}" in in_head and f"{archived_to}/proposal.md" in in_head
    assert tracked_before <= in_head  # each file of the active folder is removed in this commit
    assert git_text(root, "ls-files", "--", active).split() == []
    assert f"{active}/{META_FILE}" in ch.dirty and f"{active}/{META_FILE}" in result.committed
    assert result.already_dirty == []  # the former active folder is the change's own, though close's record names it
    assert not [line for line in dirty_now(root) if ".specworks/changes/" in line]


# @ac AC-PROJ-024.7
def test_the_change_s_own_files_are_committed_and_not_flagged_as_already_dirty(project):
    own = f"{CHANGE}/{META_FILE}"
    ch = change(project)
    ch.dirty = {own: sha(b"the record before the phase\n")}  # `.change.yaml` was dirty when the phase started
    ch.save()
    git(project, "add", "--", own)
    git(project, "commit", "-q", "-m", "record")
    set_phase(change(project), "design")  # `.change.yaml` changed again since
    assert any(line.endswith(own) for line in dirty_now(project))
    result = commit_phase(project, REF, change(project))
    assert own in result.committed and own in files_in_head(project)
    assert own not in result.already_dirty and result.already_dirty == []
