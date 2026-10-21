"""`specworks start`: a change moves to a phase only once the gates it depends on pass."""

import pytest

from helpers import REF, run_json
from specworks.workflow.gate import GateError, gates_to_start


def start(phase, *extra):
    code, data = run_json("start", phase, "--change", REF, *extra)
    return code, data


def phase_now():
    return run_json("status", "--change", REF)[1]["phase"]


# @ac AC-FLOW-014.1
@pytest.mark.parametrize(
    "current, phase, gates",
    [
        ("refine", "specify", []),  # refine has no gate
        ("specify", "design", ["specify"]),
        ("specify", "implement", ["specify", "design"]),  # skipping ahead: every phase left behind
        ("design", "design", ["specify"]),  # re-entering
        ("review", "design", ["specify"]),  # back for rework: only the gate just before
        ("review", "implement", ["design"]),
        ("implement", "implement", ["design"]),
        ("implement", "review", ["test", "code"]),  # implement's gate is the test gate, then the code gate
        ("design", "review", ["design", "test", "code"]),
        ("validate", "close", ["validate"]),
    ],
)
def test_gates_to_start(current, phase, gates):
    assert gates_to_start(current, phase) == gates


# @ac AC-FLOW-014.2
def test_start_moves_the_change_when_the_gates_pass(project):
    code, data = start("specify")
    assert code == 0 and data["started"] and data["gates"] == [] and data["from"] == "refine"
    code, data = start("design")
    assert code == 0 and [g["gate"] for g in data["gates"]] == ["specify"] and data["phase"] == "design"
    assert phase_now() == "design"


# @ac AC-FLOW-014.3
def test_a_failing_gate_leaves_the_phase_unchanged(project):
    start("specify")
    delta = project / "spec/changes" / REF / "specs/user-auth/spec.md"
    delta.write_text(delta.read_text().replace("SHALL", "should"))
    code, data = start("design")
    assert code == 1 and data["started"] is False and data["gates"][-1]["passed"] is False
    assert phase_now() == "specify"


# @ac AC-FLOW-014.3
def test_skipping_ahead_stops_at_the_first_failing_gate(project):
    start("specify")
    code, data = start("implement", "--no-run")  # design.md has no Interfaces yet
    assert code == 1 and [(g["gate"], g["passed"]) for g in data["gates"]] == [("specify", True), ("design", False)]
    assert phase_now() == "specify"


# @ac AC-FLOW-014.1, AC-FLOW-014.3
def test_going_back_for_rework_needs_only_the_gate_before(repo):
    (repo / "spec/changes" / REF / "design.md").write_text("# Design\n\n## Interfaces\n\nNone.\n")
    run_json("phase", "review", "--change", REF)
    code, data = start("implement", "--no-run")
    assert code == 0 and [g["gate"] for g in data["gates"]] == ["design"] and phase_now() == "implement", data


# @ac AC-FLOW-014.4
def test_done_is_reached_by_close_not_start(project):
    code, data = start("done")
    assert code == 1 and "specworks close" in data["error"]


# @ac AC-FLOW-014.6
def test_leaving_implement_needs_both_halves(repo):
    run_json("task", "undo", "1.2", "--change", REF)  # the test half is done, a [code] task is open
    code, data = run_json("phase", "implement", "--change", REF)
    assert code == 0, data
    code, data = start("review", "--no-run")
    assert code == 1 and data["started"] is False, data
    assert [(g["gate"], g["passed"]) for g in data["gates"]] == [("test", True), ("code", False)]
    assert phase_now() == "implement"


# @ac AC-FLOW-014.7
@pytest.mark.parametrize("half", ["test", "code"])
def test_test_and_code_cannot_be_started(project, half):
    code, data = start(half)
    assert code == 1 and "implement" in data.get("error", ""), data
    assert phase_now() == "refine"
    with pytest.raises(GateError, match="implement"):
        gates_to_start("design", half)


def gate_implement():
    return run_json("gate", "implement", "--change", REF, "--no-run")


# @ac AC-FLOW-014.8
def test_gate_implement_runs_the_test_gate_then_the_code_gate(repo):
    code, data = gate_implement()
    names = [c["name"] for c in data.get("checks", [])]
    assert code == 0 and data["passed"] is True, data
    assert names and all(n.startswith(("test: ", "code: ")) for n in names)
    assert any(n.startswith("test: ") for n in names) and any(n.startswith("code: ") for n in names)
    assert names.index(next(n for n in names if n.startswith("code: "))) > max(i for i, n in enumerate(names) if n.startswith("test: "))
    run_json("task", "undo", "1.2", "--change", REF)  # the code half fails
    code, data = gate_implement()
    assert code == 1 and any(c["name"].startswith("code: ") and not c["ok"] and c["blocking"] for c in data["checks"]), data
    run_json("task", "undo", "1.1", "--change", REF)  # the test half fails too: the code gate does not run
    code, data = gate_implement()
    assert code == 1 and not any(c["name"].startswith("code: ") for c in data["checks"]), data
    assert any(c["name"].startswith("test: ") and not c["ok"] and c["blocking"] for c in data["checks"])
