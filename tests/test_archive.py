"""Archived changes: abandon, list --archived, status, and names an archived change keeps."""

import shutil
from datetime import date

import pytest
from typer.testing import CliRunner

from helpers import REF, run_json
from specworks.cli import app
from specworks.specs import merge

runner = CliRunner()
TODAY = date(2026, 6, 1)
ARCHIVED = f".specworks/changes/archive/{TODAY.isoformat()}-{REF}"


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    # Keeps ARCHIVED right when a run crosses midnight.
    class FixedDate(date):
        @classmethod
        def today(cls):
            return TODAY

    monkeypatch.setattr(merge, "date", FixedDate)


def abandon(reason="replaced by add-sso"):
    return run_json("abandon", "--change", REF, "--reason", reason)


# @ac AC-CLI-006.4
def test_abandon_archives_without_merging(project):
    living = (project / "src/auth/docs/spec.md").read_text()
    run_json("phase", "design", "--change", REF)
    code, data = abandon()
    assert code == 0, data
    assert data["path"] == ARCHIVED and data["phase"] == "design" and data["abandoned"] == "replaced by add-sso"
    assert not (project / ".specworks/changes/active" / REF).exists()
    assert (project / "src/auth/docs/spec.md").read_text() == living
    assert not (project / "src/auth/docs/requirements.md").exists()
    meta = (project / ARCHIVED / ".change.yaml").read_text()
    assert "phase: design" in meta and "abandoned: replaced by add-sso" in meta
    assert run_json("list")[1]["changes"] == []


# @ac AC-CLI-006.4
def test_abandon_needs_a_reason(project):
    code, data = abandon("  ")
    assert code == 1 and "--reason" in data["error"]
    assert (project / ".specworks/changes/active" / REF).is_dir()


# @ac AC-CLI-002.5, AC-CLI-004.3
def test_list_archived_and_status_read_archived_changes(project):
    abandon()
    result = runner.invoke(app, ["list", "--archived"])
    assert f"{REF:<32} {TODAY.isoformat()}  abandoned in refine: replaced by add-sso" in result.output
    for ref in (REF, f"{TODAY.isoformat()}-{REF}"):
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
    code, data = run_json("new", "active", "--no-branch")
    assert code == 1 and "reserved" in data["error"] and "active" in data["error"]


# @ac AC-PROJ-020.3
def test_an_abandoned_change_moves_from_active_to_archive(project):
    assert (project / ".specworks/changes/active" / REF).is_dir()
    code, data = abandon()
    assert code == 0 and data["path"] == ARCHIVED
    assert (project / ARCHIVED / ".change.yaml").is_file()
    assert not (project / ".specworks/changes/active" / REF).exists()
    assert not (project / ".specworks/changes" / REF).exists()


# @ac AC-CLI-004.3
def test_a_leftover_copy_of_an_archived_change_is_flagged(project):
    # A close or abandon that was not committed, undone by a branch switch, leaves the folder behind.
    abandon()
    shutil.copytree(project / ARCHIVED, project / ".specworks/changes/active" / REF)
    code, data = run_json("list")
    assert data["changes"][0]["alsoArchived"] == ARCHIVED
    code, data = run_json("check", "--change", REF)
    assert any(f"an archived change has the same name ({ARCHIVED})" in i["message"] for i in data["issues"] if i["level"] == "warning")


def test_abandoning_twice_on_one_day_fails_without_moving(project):
    abandon()
    shutil.copytree(project / ARCHIVED, project / ".specworks/changes/active" / REF)
    code, data = abandon()
    assert code == 1 and "already exists in the archive" in data["error"]
    assert (project / ".specworks/changes/active" / REF).is_dir()


# @ac AC-PROJ-012.1
def test_unreadable_or_misnamed_archive_folders_are_left_out(project):
    abandon()
    (project / ".specworks/changes/archive/2026-01-01-broken").mkdir()
    (project / ".specworks/changes/archive/2026-01-01-broken/.change.yaml").write_text("- not a mapping\n")
    (project / ".specworks/changes/archive/notes").mkdir()
    (project / ".specworks/changes/archive/notes/.change.yaml").write_text("name: notes\n")
    code, data = run_json("list", "--archived")
    assert code == 0 and [c["name"] for c in data["changes"]] == [REF]


# @ac AC-PROJ-012.2
def test_archived_changes_are_listed_oldest_first(project):
    abandon()  # archived on TODAY
    older = project / ".specworks/changes/archive/2026-01-02-zz-older"  # its name sorts after REF, its date before
    older.mkdir()
    (older / ".change.yaml").write_text("name: zz-older\ncreated: '2026-01-01T10:00:00'\nphase: done\n")
    code, data = run_json("list", "--archived")
    assert code == 0 and [c["name"] for c in data["changes"]] == ["zz-older", REF]
