"""Archived changes: abandon, list --archived, status, and names an archived change keeps."""

import pytest

from helpers import REF, run_json
from support.archive import ARCHIVED, abandon, make_fixed_today


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    return make_fixed_today(monkeypatch)


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
