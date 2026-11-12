"""
Reopening a closed change (REQ-PROJ-033) and recording why (REQ-PROJ-034).
"""

import re
import shutil

import pytest
import yaml

from specworks.core.changes import META_FILE, ChangeError, ChangeNotFound, archived_as, half_error, load_change, reopen_change
from specworks.core.config import load_config
from specworks.core.events import trace_id
from specworks.specs.merge import archive_change
from support.close_phase import snapshot
from support.commit import CHANGE, REF, make_project, sha
from support.reopen import DAY, EVENTS, commit_all, make_archived

ARCHIVED = f".specworks/changes/archive/{DAY}-{REF}"
AT = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


def active_meta(root, name=REF):
    return yaml.safe_load((root / ".specworks/changes/active" / name / META_FILE).read_text(encoding="utf-8"))


# @ac AC-PROJ-033.1
def test_a_closed_change_goes_back_to_the_active_folder_in_review(project):
    closed = make_archived(project, REF)
    cfg = load_config(project)
    assert closed.phase == "done"
    reopened = reopen_change(cfg, REF, "CI lint failed", "review", project)
    active = project / CHANGE
    assert reopened.phase == "review" and reopened.path == active
    assert (active / "proposal.md").read_text(encoding="utf-8") == f"# Proposal: {REF}\n"
    assert (active / "events.jsonl").read_text(encoding="utf-8") == EVENTS
    assert not (project / ARCHIVED).exists()
    back = load_change(cfg, REF)
    assert back.phase == "review" and back.created == closed.created
    assert archived_as(cfg, REF) is None


# @ac AC-PROJ-033.1
def test_the_archive_folder_name_names_the_change_too(project):
    make_archived(project, REF)
    reopen_change(load_config(project), f"{DAY}-{REF}", "CI lint failed", "review", project)
    assert load_change(load_config(project), REF).phase == "review"
    assert not (project / ARCHIVED).exists()


# @ac AC-PROJ-033.2
@pytest.mark.parametrize("phase", ["refine", "implement"])
def test_a_change_reopens_to_the_phase_given(project, phase):
    make_archived(project, REF)
    cfg = load_config(project)
    reopened = reopen_change(cfg, REF, "start again", phase, project)
    assert reopened.phase == phase
    assert load_change(cfg, REF).phase == phase


# @ac AC-PROJ-033.3
@pytest.mark.parametrize(
    ("phase", "message"),
    [
        ("done", "only through `specworks close`"),
        ("test", half_error("test")),
        ("code", half_error("code")),
        ("no-such-phase", "unknown phase 'no-such-phase'"),
    ],
)
def test_a_phase_set_phase_refuses_is_refused_and_the_change_stays_archived(project, phase, message):
    make_archived(project, REF)
    cfg = load_config(project)
    before = snapshot(project)
    with pytest.raises(ChangeError, match=re.escape(message)):
        reopen_change(cfg, REF, "start again", phase, project)
    assert snapshot(project) == before
    assert archived_as(cfg, REF) is not None and not (project / CHANGE).exists()


# @ac AC-PROJ-033.4
def test_an_active_change_is_not_reopened(project):
    cfg = load_config(project)
    before = snapshot(project)
    with pytest.raises(ChangeError, match="(?i)active"):
        reopen_change(cfg, REF, "start again", "review", project)
    assert snapshot(project) == before


# @ac AC-PROJ-033.4
def test_an_abandoned_change_is_not_reopened(project):
    make_archived(project, REF, abandoned="not needed")
    cfg = load_config(project)
    before = snapshot(project)
    with pytest.raises(ChangeError, match="(?i)abandoned"):
        reopen_change(cfg, REF, "start again", "review", project)
    assert snapshot(project) == before


# @ac AC-PROJ-033.4
def test_an_unknown_change_is_not_found(project):
    make_archived(project, REF)
    cfg = load_config(project)
    before = snapshot(project)
    with pytest.raises(ChangeNotFound, match="no-such-change"):
        reopen_change(cfg, "no-such-change", "start again", "review", project)
    assert snapshot(project) == before


# @ac AC-PROJ-033.5
def test_a_name_an_active_change_already_has_is_refused_and_both_folders_stay(project):
    make_archived(project, REF)
    (project / CHANGE).mkdir()
    (project / CHANGE / "notes.md").write_text("a new change with the same name\n", encoding="utf-8")
    cfg = load_config(project)
    before = snapshot(project)
    with pytest.raises(ChangeError, match=r"(?i)active.*exist|exist.*active"):
        reopen_change(cfg, REF, "start again", "review", project)
    assert snapshot(project) == before


# @ac AC-PROJ-033.6
def test_the_record_holds_the_files_dirty_before_the_move_not_the_ones_the_move_removed(project):
    make_archived(project, REF)
    commit_all(project)  # the close is committed
    (project / "notes.txt").write_bytes(b"notes, edited\n")
    reopen_change(load_config(project), REF, "start again", "review", project)
    assert active_meta(project)["dirty"] == {"notes.txt": sha(b"notes, edited\n")}
    assert load_change(load_config(project), REF).dirty == {"notes.txt": sha(b"notes, edited\n")}


# @ac AC-PROJ-033.7
def test_a_failed_move_raises_and_leaves_the_change_archived_as_it_was(project, monkeypatch):
    make_archived(project, REF)
    cfg = load_config(project)
    before = snapshot(project)

    def broken(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(shutil, "move", broken)
    with pytest.raises(OSError, match="disk full"):
        reopen_change(cfg, REF, "start again", "review", project)
    assert snapshot(project) == before
    assert archived_as(cfg, REF) is not None and not (project / CHANGE).exists()


# @ac AC-PROJ-033.8
def test_the_events_and_the_trace_id_come_back_with_the_change(project):
    closed = make_archived(project, REF)
    cfg = load_config(project)
    before = trace_id("(top)", closed)
    reopened = reopen_change(cfg, REF, "start again", "review", project)
    assert (project / CHANGE / "events.jsonl").read_text(encoding="utf-8").splitlines() == EVENTS.splitlines()
    assert trace_id("(top)", reopened) == trace_id("(top)", load_change(cfg, REF)) == before


# @ac AC-PROJ-034.1
def test_the_reason_the_time_and_the_phase_are_recorded(project):
    make_archived(project, REF)
    cfg = load_config(project)
    reopen_change(cfg, REF, "CI lint failed", "review", project)
    entries = active_meta(project)["reopened"]
    assert len(entries) == 1
    assert entries[0]["reason"] == "CI lint failed" and entries[0]["phase"] == "review" and AT.match(str(entries[0]["at"]))
    loaded = load_change(cfg, REF).reopened
    assert [(r.reason, r.phase) for r in loaded] == [("CI lint failed", "review")] and AT.match(loaded[0].at)


# @ac AC-PROJ-034.2
def test_a_change_reopened_twice_keeps_both_reasons_oldest_first(project):
    make_archived(project, REF)
    cfg = load_config(project)
    reopen_change(cfg, REF, "CI lint failed", "review", project)
    archive_change(load_change(cfg, REF), cfg.archive_path, "2026-06-02")  # closed again
    assert [r.reason for r in archived_as(cfg, REF).reopened] == ["CI lint failed"]
    reopen_change(cfg, REF, "the API was wrong", "implement", project)
    entries = load_change(cfg, REF).reopened
    assert [(r.reason, r.phase) for r in entries] == [("CI lint failed", "review"), ("the API was wrong", "implement")]


# @ac AC-PROJ-034.3
@pytest.mark.parametrize("reason", ["", "   "])
def test_a_blank_reason_is_refused_and_the_change_stays_archived(project, reason):
    make_archived(project, REF)
    cfg = load_config(project)
    before = snapshot(project)
    with pytest.raises(ChangeError, match="(?i)reason"):
        reopen_change(cfg, REF, reason, "review", project)
    assert snapshot(project) == before
    assert archived_as(cfg, REF) is not None and not (project / CHANGE).exists()


# @ac AC-PROJ-034.4
def test_metadata_without_a_reopened_entry_loads_with_none(project):
    (project / CHANGE / META_FILE).write_text(f"name: {REF}\ncreated: '2026-01-01T00:00:00'\nphase: design\n", encoding="utf-8")
    cfg = load_config(project)
    change = load_change(cfg, REF)
    assert change.reopened == []
    change.save()
    assert "reopened" not in active_meta(project)  # an empty list is not written
