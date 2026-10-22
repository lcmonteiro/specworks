"""Archived changes: abandon, list --archived, status, and names an archived change keeps."""

import shutil
from datetime import date

from typer.testing import CliRunner

from helpers import REF, run_json
from specworks.cli import app

runner = CliRunner()
ARCHIVED = f"spec/changes/archive/{date.today().isoformat()}-{REF}"


def abandon(reason="replaced by add-sso"):
    return run_json("abandon", "--change", REF, "--reason", reason)


# @ac AC-CLI-006.4
def test_abandon_archives_without_merging(project):
    living = (project / "src/auth/docs/spec.md").read_text()
    run_json("phase", "design", "--change", REF)
    code, data = abandon()
    assert code == 0, data
    assert data["path"] == ARCHIVED and data["phase"] == "design" and data["abandoned"] == "replaced by add-sso"
    assert not (project / "spec/changes" / REF).exists()
    assert (project / "src/auth/docs/spec.md").read_text() == living
    assert not (project / "src/auth/docs/requirements.md").exists()
    meta = (project / ARCHIVED / ".change.yaml").read_text()
    assert "phase: design" in meta and "abandoned: replaced by add-sso" in meta
    assert run_json("list")[1]["changes"] == []


# @ac AC-CLI-006.4
def test_abandon_needs_a_reason(project):
    code, data = abandon("  ")
    assert code == 1 and "--reason" in data["error"]
    assert (project / "spec/changes" / REF).is_dir()


# @ac AC-CLI-002.5, AC-CLI-004.3
def test_list_archived_and_status_read_archived_changes(project):
    abandon()
    result = runner.invoke(app, ["list", "--archived"])
    assert f"{REF:<32} {date.today().isoformat()}  abandoned in refine: replaced by add-sso" in result.output
    for ref in (REF, f"{date.today().isoformat()}-{REF}"):
        code, data = run_json("status", "--change", ref)
        assert code == 0 and data["archived"] is True and data["path"] == ARCHIVED
    result = runner.invoke(app, ["status", "--change", REF])
    assert f"{REF} (phase: refine), abandoned: replaced by add-sso, archived at {ARCHIVED}" in result.output


# @ac AC-CLI-002.4
def test_other_commands_say_the_change_is_archived(project):
    abandon()
    code, data = run_json("gate", "specify", "--change", REF)
    assert code == 1 and f"change '{REF}' is archived at {ARCHIVED}, not active" in data["error"]
    code, data = run_json("status", "--change", "nope")
    assert code == 1 and "not found in any module, active or archived" in data["error"]


# @ac AC-PROJ-010.4
def test_new_refuses_an_archived_name_and_the_archive_folder(project):
    abandon()
    code, data = run_json("new", REF, "--no-branch")
    assert code == 1 and f"was archived at {ARCHIVED}" in data["error"]
    code, data = run_json("new", "archive", "--no-branch")
    assert code == 1 and "'archive' is reserved" in data["error"]


# @ac AC-CLI-004.3
def test_a_leftover_copy_of_an_archived_change_is_flagged(project):
    # A close or abandon that was not committed, undone by a branch switch, leaves the folder behind.
    abandon()
    shutil.copytree(project / ARCHIVED, project / "spec/changes" / REF)
    code, data = run_json("list")
    assert data["changes"][0]["alsoArchived"] == ARCHIVED
    code, data = run_json("check", "--change", REF)
    assert any(f"an archived change has the same name ({ARCHIVED})" in i["message"] for i in data["issues"] if i["level"] == "warning")


def test_abandoning_twice_on_one_day_fails_without_moving(project):
    abandon()
    shutil.copytree(project / ARCHIVED, project / "spec/changes" / REF)
    code, data = abandon()
    assert code == 1 and "already exists in the archive" in data["error"]
    assert (project / "spec/changes" / REF).is_dir()


# @ac AC-PROJ-012.1
def test_unreadable_or_misnamed_archive_folders_are_left_out(project):
    abandon()
    (project / "spec/changes/archive/2026-01-01-broken").mkdir()
    (project / "spec/changes/archive/2026-01-01-broken/.change.yaml").write_text("- not a mapping\n")
    (project / "spec/changes/archive/notes").mkdir()
    (project / "spec/changes/archive/notes/.change.yaml").write_text("name: notes\n")
    code, data = run_json("list", "--archived")
    assert code == 0 and [c["name"] for c in data["changes"]] == [REF]


# @ac AC-PROJ-012.2
def test_archived_changes_are_listed_oldest_first(project):
    abandon()  # archived today
    older = project / "spec/changes/archive/2026-01-02-zz-older"  # its name sorts after REF, its date before
    older.mkdir()
    (older / ".change.yaml").write_text("name: zz-older\ncreated: '2026-01-01T10:00:00'\nphase: done\n")
    code, data = run_json("list", "--archived")
    assert code == 0 and [c["name"] for c in data["changes"]] == ["zz-older", REF]
