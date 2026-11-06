"""A change reopened after its close may touch the IDs its own earlier close added, changed or removed (REQ-SPECS-017)."""

import re

import pytest

from samples import DELTA, LIVING
from specworks.core.changes import load_change
from specworks.core.workspace import load_workspace
from specworks.specs.check import collect
from specworks.specs.merge import MergeError, close_change, plan_merge
from specworks.specs.specfile import parse_spec
from support.close_phase import snapshot
from support.propose import errors, make_change, make_project, run_json

REF = "add-password-reset"
REQUIREMENTS = "src/auth/docs/requirements.md"
SPEC = "src/auth/docs/spec.md"


def block(rid, text="The system SHALL email a single-use reset link valid for 30 minutes.", title="Password reset"):
    n = rid[-3:]
    return (
        f"### Requirement: {rid} {title}\n{text}\n\n"
        f"#### Scenario: AC-AUTH-{n}.1 Request reset\n- **WHEN** a user asks for a reset\n- **THEN** a link is emailed\n"
    )


def removed(rid):
    return f"### Requirement: {rid} Password reset\n**Reason**: replaced by SSO\n**Migration**: use SSO\n"


def delta(**sections):
    return "# Spec Delta: user-auth\n\n" + "".join(f"## {name.upper()} Requirements\n\n{body}\n" for name, body in sections.items())


def history(*lines):
    return "# Requirements: user-auth\n\n## History\n\n" + "".join(f"- {line}\n" for line in lines)


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = make_project(tmp_path, monkeypatch)
    make_change(root)
    return root


def setup(project, delta_text, living=LIVING, lines=()):
    (project / SPEC).write_text(living, encoding="utf-8")
    (project / REQUIREMENTS).write_text(history(*lines), encoding="utf-8")
    (project / f".specworks/changes/active/{REF}/specs/user-auth/spec.md").write_text(delta_text, encoding="utf-8")


def problems(rid):
    """The errors `specworks check` gives about one ID: they all start with it."""
    _, data = run_json("check", "--change", REF)
    return [m for m in errors(data) if m.startswith(rid)]


def modified_warnings():
    _, data = run_json("check", "--change", REF)
    return [i["message"] for i in data["issues"] if i["level"] == "warning" and i["message"].startswith("REQ-AUTH-002 was MODIFIED by")]


# @ac AC-SPECS-017.1
def test_an_id_the_change_added_itself_can_be_added_again(project):
    setup(project, delta(added=block("REQ-AUTH-003", "The system SHALL email a reset link.")), LIVING + "\n" + block("REQ-AUTH-003"), [f"2026-01-02 09:00:00 `{REF}`: ADDED REQ-AUTH-003"])
    assert problems("REQ-AUTH-003") == []


# @ac AC-SPECS-017.2
def test_an_id_the_change_removed_itself_can_be_removed_again(project):
    setup(project, delta(removed=removed("REQ-AUTH-003")), LIVING, [f"2026-01-02 09:00:00 `{REF}`: REMOVED REQ-AUTH-003"])
    assert problems("REQ-AUTH-003") == []


# @ac AC-SPECS-017.3
def test_an_id_another_change_added_still_exists(project):
    setup(project, delta(added=block("REQ-AUTH-003")), LIVING + "\n" + block("REQ-AUTH-003"), ["2026-01-02 09:00:00 `other`: ADDED REQ-AUTH-003"])
    assert [m for m in problems("REQ-AUTH-003") if "already exists" in m]


# @ac AC-SPECS-017.3
def test_an_id_this_change_never_removed_is_not_in_the_living_spec(project):
    setup(project, delta(removed=removed("REQ-AUTH-003")), LIVING, ["2026-01-02 09:00:00 `other`: REMOVED REQ-AUTH-003"])
    assert [m for m in problems("REQ-AUTH-003") if "is not in the living spec" in m]


# @ac AC-SPECS-017.4
def test_the_changes_own_earlier_edit_is_not_one_made_after_it_started(project):
    setup(project, DELTA, LIVING, [f"2999-01-01 09:00:00 `{REF}`: MODIFIED REQ-AUTH-002"])
    assert modified_warnings() == []


# @ac AC-SPECS-017.4
def test_another_changes_edit_at_the_same_time_still_warns(project):
    setup(project, DELTA, LIVING, [f"2999-01-01 09:00:00 `{REF}`: MODIFIED REQ-AUTH-002", "2999-01-01 09:00:00 `stricter-lockout`: MODIFIED REQ-AUTH-002"])
    assert [w for w in modified_warnings() if "stricter-lockout" in w]


# @ac AC-SPECS-017.8
def test_an_id_another_change_removed_is_never_reused_even_if_this_one_added_it_first(project):
    setup(project, delta(added=block("REQ-AUTH-005")), LIVING, [f"2026-01-02 09:00:00 `{REF}`: ADDED REQ-AUTH-005", "2026-02-03 09:00:00 `other`: REMOVED REQ-AUTH-005"])
    assert [m for m in problems("REQ-AUTH-005") if "never reused" in m]


def close(project):
    ws = load_workspace(project)
    change = load_change(ws.current.config, REF)
    return ws, change, plan_merge(ws, change, collect(ws, change), REF)


# @ac AC-SPECS-017.5
def test_closing_again_replaces_the_ids_the_change_added_in_place_and_keeps_the_history(project):
    living = LIVING + "\n" + block("REQ-AUTH-004", "The system SHALL log resets.", "Audit") + "\n" + block("REQ-AUTH-005") + "\n" + block("REQ-AUTH-006", "The system SHALL rate-limit resets.", "Rate")
    first = f"2026-01-02 09:00:00 `{REF}`: ADDED REQ-AUTH-005"
    setup(project, delta(added=block("REQ-AUTH-005", "The system SHALL email a reset link valid for 15 minutes.")), living, [first])
    ws, change, merges = close(project)
    close_change(merges, change, ws.current.config.archive_path)
    text = (project / SPEC).read_text(encoding="utf-8")
    ids = [r.id for r in parse_spec(text).requirements]
    assert ids == ["REQ-AUTH-001", "REQ-AUTH-002", "REQ-AUTH-004", "REQ-AUTH-005", "REQ-AUTH-006"]
    assert "valid for 15 minutes" in parse_spec(text).by_id()["REQ-AUTH-005"].description
    lines = [ln for ln in (project / REQUIREMENTS).read_text(encoding="utf-8").splitlines() if ln.startswith("- 20")]
    assert lines[0] == f"- {first}"
    assert re.fullmatch(rf"- \d{{4}}-\d\d-\d\d \d\d:\d\d:\d\d `{REF}`: MODIFIED REQ-AUTH-005", lines[1])


# @ac AC-SPECS-017.6
def test_an_id_the_change_removed_before_is_removed_again_without_a_new_history_entry_for_it(project):
    setup(project, delta(removed=removed("REQ-AUTH-003")), LIVING, [f"2026-01-02 09:00:00 `{REF}`: REMOVED REQ-AUTH-003"])
    ws, change, merges = close(project)
    close_change(merges, change, ws.current.config.archive_path)
    lines = [ln for ln in (project / REQUIREMENTS).read_text(encoding="utf-8").splitlines() if ln.startswith("- 20")]
    assert len(lines) == 2 and "REQ-AUTH-003" not in lines[1]


# @ac AC-SPECS-017.7
def test_an_id_another_change_added_stops_the_close_and_writes_nothing(project):
    setup(project, delta(added=block("REQ-AUTH-003")), LIVING + "\n" + block("REQ-AUTH-003"), ["2026-01-02 09:00:00 `other`: ADDED REQ-AUTH-003"])
    ws = load_workspace(project)
    change = load_change(ws.current.config, REF)
    before = snapshot(project)
    with pytest.raises(MergeError, match="already in the living spec"):
        plan_merge(ws, change, collect(ws, change), REF)
    assert snapshot(project) == before
