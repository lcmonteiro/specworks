"""`specworks start`: a change moves to a phase only once the gates it depends on pass."""

import pytest

from helpers import REF, run_json
from specworks.workflow.gate import gates_to_start


def start(phase, *extra):
    code, data = run_json("start", phase, "--change", REF, *extra)
    return code, data


def phase_now():
    return run_json("status", "--change", REF)[1]["phase"]


@pytest.mark.parametrize(
    "current, phase, gates",
    [
        ("refine", "specify", []),  # refine has no gate
        ("specify", "design", ["specify"]),
        ("specify", "test", ["specify", "design"]),  # skipping ahead: every phase left behind
        ("design", "design", ["specify"]),  # re-entering
        ("review", "design", ["specify"]),  # back for rework: only the gate just before
        ("review", "code", ["test"]),
        ("validate", "close", ["validate"]),
    ],
)
def test_gates_to_start(current, phase, gates):
    assert gates_to_start(current, phase) == gates


def test_start_moves_the_change_when_the_gates_pass(project):
    code, data = start("specify")
    assert code == 0 and data["started"] and data["gates"] == [] and data["from"] == "refine"
    code, data = start("design")
    assert code == 0 and [g["gate"] for g in data["gates"]] == ["specify"] and data["phase"] == "design"
    assert phase_now() == "design"


def test_a_failing_gate_leaves_the_phase_unchanged(project):
    start("specify")
    delta = project / "spec/changes" / REF / "specs/user-auth/spec.md"
    delta.write_text(delta.read_text().replace("SHALL", "should"))
    code, data = start("design")
    assert code == 1 and data["started"] is False and data["gates"][-1]["passed"] is False
    assert phase_now() == "specify"


def test_skipping_ahead_stops_at_the_first_failing_gate(project):
    start("specify")
    code, data = start("test", "--no-run")  # design.md has no Interfaces yet
    assert code == 1 and [(g["gate"], g["passed"]) for g in data["gates"]] == [("specify", True), ("design", False)]
    assert phase_now() == "specify"


def test_going_back_for_rework_needs_only_the_gate_before(repo):
    run_json("phase", REF, "review")
    code, data = start("code", "--no-run")
    assert code == 0 and [g["gate"] for g in data["gates"]] == ["test"] and phase_now() == "code"


def test_done_is_reached_by_close_not_start(project):
    code, data = start("done")
    assert code == 1 and "specworks close" in data["error"]
