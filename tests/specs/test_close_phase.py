"""Close phase: capability registration, delta merge into living specs, requirements index, archive."""

import re
import shutil
from datetime import date

import pytest

from helpers import REF, run_json
from specworks.core.changes import load_change
from specworks.core.workspace import load_workspace
from specworks.specs.check import collect
from specworks.specs.merge import MergeError, apply_delta, close_change, plan_merge
from specworks.specs.specfile import parse_spec
from support.close_phase import CHANGE_DIR, make_ready, snapshot


@pytest.fixture
def ready(repo):
    return make_ready(repo)


# @ac AC-SPECS-013.1
def test_close_merges_indexes_and_archives(ready):
    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 0, data
    today = date.today().isoformat()
    assert data["archivedTo"] == f".specworks/changes/archive/{today}-{REF}"

    living = parse_spec((ready / "src/auth/docs/spec.md").read_text())
    assert [(r.id, r.title) for r in living.requirements] == [
        ("REQ-AUTH-001", "Password login"),
        ("REQ-AUTH-002", "Lockout after failures"),
        ("REQ-AUTH-003", "Password reset"),
    ]
    assert "3 failed attempts" in living.by_id()["REQ-AUTH-002"].description

    index = (ready / "src/auth/docs/requirements.md").read_text()
    assert "| REQ-AUTH-003 | Password reset | AC-AUTH-003.1, AC-AUTH-003.2 |" in index
    assert re.search(rf"^- {today} \d\d:\d\d:\d\d `{REF}`: ADDED REQ-AUTH-003; MODIFIED REQ-AUTH-002$", index, re.M)

    archived = ready / data["archivedTo"]
    assert (archived / "proposal.md").is_file() and "phase: done" in (archived / ".change.yaml").read_text()
    assert not (ready / CHANGE_DIR).exists()
    code, data = run_json("list")
    assert data["changes"] == []
    code, data = run_json("list", "--archived")
    assert [(c["name"], c["phase"], c.get("archived")) for c in data["changes"]] == [(REF, "done", True)]
    code, data = run_json("spec", "show", "user-auth")
    assert data["nextId"] == "REQ-AUTH-004"


# @ac AC-SPECS-013.5
def test_the_history_line_holds_the_close_time(ready):
    index = ready / "src/auth/docs/requirements.md"
    index.write_text("# Requirements: user-auth\n\n## History\n\n- 2026-01-02 `older-change`: ADDED REQ-AUTH-002\n")
    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 0, data
    history = index.read_text().split("## History", 1)[1].strip().splitlines()
    assert history[0] == "- 2026-01-02 `older-change`: ADDED REQ-AUTH-002"
    assert re.fullmatch(rf"- {date.today().isoformat()} \d\d:\d\d:\d\d `{REF}`: .*", history[1])


# @ac AC-SPECS-013.6
def test_a_pipe_in_a_title_stays_in_its_index_cell(ready):
    delta = ready / CHANGE_DIR / "specs/user-auth/spec.md"
    delta.write_text(delta.read_text().replace("REQ-AUTH-003 Password reset", "REQ-AUTH-003 Read | write"))
    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 0, data
    assert r"| REQ-AUTH-003 | Read \| write | AC-AUTH-003.1, AC-AUTH-003.2 |" in (ready / "src/auth/docs/requirements.md").read_text()
    assert "### Requirement: REQ-AUTH-003 Read | write" in (ready / "src/auth/docs/spec.md").read_text()


# @ac AC-SPECS-013.3
def test_close_refuses_to_merge_into_a_broken_living_spec(ready):
    living = ready / "src/auth/docs/spec.md"
    living.write_text(living.read_text() + "\n### Requirement: Search by title\nThe system SHALL search.\n")
    before = snapshot(ready)
    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 1
    assert "src/auth/docs/spec.md is not a valid living spec" in data["error"] and "no 'REQ-<prefix>-NNN' ID" in data["error"]
    assert snapshot(ready) == before


DELTA_MODIFY_MISSING = "## MODIFIED Requirements\n\n### Requirement: REQ-AUTH-009 Ghost\nThe system SHALL x.\n"


class FakeDelta:
    def __init__(self, text):
        self.doc = parse_spec(text)
        self.cap = type("Cap", (), {"ref": "user-auth"})()


@pytest.mark.parametrize(
    "delta, message",
    [
        (DELTA_MODIFY_MISSING, "REQ-AUTH-009 is MODIFIED but not in the living spec"),
        ("## REMOVED Requirements\n\n### Requirement: REQ-AUTH-009 Ghost\n", "REQ-AUTH-009 is REMOVED but not in the living spec"),
        ("## ADDED Requirements\n\n### Requirement: REQ-AUTH-001 Dup\nThe system SHALL x.\n", "REQ-AUTH-001 is ADDED but already"),
    ],
)
# @ac AC-SPECS-013.3
def test_merge_errors(delta, message):
    living = "# user-auth\n\n## Requirements\n\n### Requirement: REQ-AUTH-001 Login\nThe system SHALL log in.\n"
    with pytest.raises(MergeError, match=message):
        apply_delta(living, FakeDelta(delta))


# @ac AC-SPECS-013.2
def test_removed_requirement_is_deleted_and_other_sections_kept():
    living = (
        "# user-auth\n\nIntro.\n\n## Requirements\n\n### Requirement: REQ-AUTH-001 A\nThe system SHALL a.\n\n"
        "### Requirement: REQ-AUTH-002 B\nThe system SHALL b.\n\n## Notes\n\nKeep me.\n"
    )
    text, added, modified, removed = apply_delta(
        living, FakeDelta("## REMOVED Requirements\n\n### Requirement: REQ-AUTH-001 A\n**Reason**: x\n**Migration**: y\n")
    )
    assert removed == ["REQ-AUTH-001"] and "REQ-AUTH-001" not in text
    assert text.startswith("# user-auth\n\nIntro.\n") and text.endswith("## Notes\n\nKeep me.\n")



MODIFY_A = "## MODIFIED Requirements\n\n### Requirement: REQ-AUTH-001 A\nThe system SHALL a2.\n\n#### Scenario: AC-AUTH-001.1 s\n- **WHEN** w\n- **THEN** t\n"


@pytest.mark.parametrize(
    "delta", [MODIFY_A, "## REMOVED Requirements\n\n### Requirement: REQ-AUTH-001 A\n**Reason**: x\n**Migration**: y\n"]
)
# @ac AC-SPECS-013.2
def test_a_heading_after_the_last_requirement_is_kept(delta):
    living = "# user-auth\n\n## Requirements\n\n### Requirement: REQ-AUTH-001 A\nThe system SHALL a.\n\n### Notes\nKeep me.\n"
    text, *_ = apply_delta(living, FakeDelta(delta))
    assert text.endswith("### Notes\nKeep me.\n") and "SHALL a." not in text


# @ac AC-SPECS-013.2
def test_merge_only_tidies_blank_lines_where_it_splices():
    living = (
        "# user-auth\n\n## Purpose\n\n```\nline 1\n\n\n\nline 2\n```\n\n## Requirements\n\n"
        "### Requirement: REQ-AUTH-001 A\nThe system SHALL a.\n\n\n\n## Notes\n\n\nKeep the spacing.\n"
    )
    text, *_ = apply_delta(living, FakeDelta(MODIFY_A))
    assert "line 1\n\n\n\nline 2" in text and "## Notes\n\n\nKeep the spacing.\n" in text
    assert "- **THEN** t\n\n## Notes" in text  # one blank line where the new block meets the next section

# @ac AC-SPECS-013.2
def test_headings_in_a_code_fence_are_text_when_merging():
    living = (
        "# user-auth\n\n## Requirements\n\n### Requirement: REQ-AUTH-001 A\nThe system SHALL read:\n\n"
        "```markdown\n## Example\n### Requirement: REQ-AUTH-009 not real\n```\n\n## Notes\n\nKeep me.\n"
    )
    text, added, _, removed = apply_delta(
        living,
        FakeDelta(
            "## ADDED Requirements\n\n### Requirement: REQ-AUTH-002 B\nThe system SHALL b.\n\n"
            "## REMOVED Requirements\n\n### Requirement: REQ-AUTH-001 A\n**Reason**: x\n**Migration**: y\n"
        ),
    )
    assert added == ["REQ-AUTH-002"] and removed == ["REQ-AUTH-001"]
    assert text == "# user-auth\n\n## Requirements\n\n### Requirement: REQ-AUTH-002 B\nThe system SHALL b.\n\n## Notes\n\nKeep me.\n"


# @ac AC-SPECS-013.4
def test_a_taken_archive_folder_fails_before_anything_is_written(ready):
    # e.g. a change with the same name was already closed today
    (ready / f".specworks/changes/archive/{date.today().isoformat()}-{REF}").mkdir(parents=True)
    before = snapshot(ready)
    for extra in (["--dry-run"], []):
        code, data = run_json("close", "--change", REF, "--base", "main", *extra)
        assert code == 1 and "already exists" in data["error"]
    assert snapshot(ready) == before


# @ac AC-SPECS-013.4
def test_a_failed_archive_puts_the_living_docs_back(ready, monkeypatch):
    import shutil

    before = snapshot(ready)
    real_move, calls = shutil.move, []

    def move_failing_once(src, dst):
        calls.append(src)
        if len(calls) == 1:
            raise OSError("disk full")
        return real_move(src, dst)

    monkeypatch.setattr(shutil, "move", move_failing_once)
    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 1 and "disk full" in data["error"]
    assert snapshot(ready) == before  # living spec, requirements.md and the change's phase untouched
    code, data = run_json("close", "--change", REF, "--base", "main")  # and closing again works
    assert code == 0, data


# @ac AC-SPECS-010.2
def test_a_removed_id_is_never_handed_out_again(project):
    shutil.rmtree(project / CHANGE_DIR)  # its delta takes REQ-AUTH-003; only the living spec counts here
    run_json("new", "drop-lockout", "--no-branch")
    delta = project / ".specworks/changes/active/drop-lockout/specs/user-auth"
    delta.mkdir(parents=True)
    (delta / "spec.md").write_text("## REMOVED Requirements\n\n### Requirement: REQ-AUTH-002 Lockout\n**Reason**: x\n**Migration**: y\n")
    ws = load_workspace(project)
    change = load_change(ws.current.config, "drop-lockout")
    close_change(plan_merge(ws, change, collect(ws, change), "drop-lockout"), change, ws.current.config.archive_path)
    assert "REMOVED REQ-AUTH-002" in (project / "src/auth/docs/requirements.md").read_text()
    code, data = run_json("spec", "show", "user-auth")
    assert [r["id"] for r in data["requirements"]] == ["REQ-AUTH-001"] and data["nextId"] == "REQ-AUTH-003"
