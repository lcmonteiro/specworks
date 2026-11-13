import pytest

from specworks.cli import app
from support.propose import make_change, make_project, run_json, runner


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


@pytest.fixture
def change(project):
    return make_change(project)


# @ac AC-FLOW-002.3
def test_instructions_for_specs_list_capabilities(project):
    code, data = run_json("instructions", "specs", "--change", "add-password-reset")
    caps = {c["ref"]: c for c in data["capabilities"]}
    assert caps["user-auth"]["nextId"] == "REQ-AUTH-003"
    assert "REQ-<prefix>-NNN" in data["instruction"]


# @ac AC-FLOW-001.1
def test_status_after_planning(change):
    code, data = run_json("status", "--change", "add-password-reset")
    states = {a["id"]: a["status"] for a in data["artifacts"]}
    assert states == {
        "refinement": "ready",
        "proposal": "done",
        "specs": "done",
        "design": "ready",
        "tasks": "done",
        "traceability": "ready",
        "review": "ready",
        "validation": "blocked",
        "inspection": "ready",
    }


# @ac AC-FLOW-001.5
def test_ac_flow_001_5_validation_is_optional_then_done(change):
    (change / "review.md").write_text("# Review: add-password-reset\n\n## Findings\n\nNone.\n", encoding="utf-8")
    code, data = run_json("status", "--change", "add-password-reset")
    validation = {a["id"]: a for a in data["artifacts"]}["validation"]
    assert code == 0 and (validation["status"], validation["optional"]) == ("ready", True), validation
    (change / "validation.md").write_text("# Validation: add-password-reset\n\n## Findings\n\nNone.\n", encoding="utf-8")
    code, data = run_json("status", "--change", "add-password-reset")
    assert {a["id"]: a["status"] for a in data["artifacts"]}["validation"] == "done"


# @ac AC-FLOW-001.6
def test_ac_flow_001_6_inspection_is_optional_then_done(change):
    code, data = run_json("status", "--change", "add-password-reset")
    inspection = {a["id"]: a for a in data["artifacts"]}["inspection"]
    assert code == 0 and (inspection["status"], inspection["optional"]) == ("ready", True), inspection
    (change / "inspection.md").write_text("# Inspection: add-password-reset\n\n## Findings\n\n- [ ] I1 **question** why?\n", encoding="utf-8")
    code, data = run_json("status", "--change", "add-password-reset")
    assert code == 0 and {a["id"]: a["status"] for a in data["artifacts"]}["inspection"] == "done", data


# @ac AC-FLOW-001.4
def test_status_shows_the_halves_of_implement(change):
    (change / "tasks.md").write_text(
        "# Tasks\n\n## 1. Reset\n\n"
        "- [x] 1.1 [test] Tests for AC-AUTH-003.1\n- [x] 1.2 [test] Tests for AC-AUTH-003.2\n- [x] 1.3 [test] Tests for AC-AUTH-002.1\n"
        "- [x] 1.4 [code] Implement REQ-AUTH-003\n- [ ] 1.5 [code] Lower the lockout (REQ-AUTH-002)\n"
        "- [ ] 1.6 [code] Wire the email\n- [ ] 1.7 [code] Log resets\n- [ ] 1.8 Update the README\n"
    )
    code, data = run_json("status", "--change", "add-password-reset")
    assert code == 0 and data.get("halves") is None  # not in implement yet
    code, data = run_json("phase", "implement", "--change", "add-password-reset")
    assert code == 0, data
    code, data = run_json("status", "--change", "add-password-reset")
    assert data["halves"] == {"test": {"done": 3, "total": 3}, "code": {"done": 1, "total": 4}}
    text = runner.invoke(app, ["status", "--change", "add-password-reset"]).output
    assert "test 3/3, code 1/4" in text


# @ac AC-FLOW-001.3, AC-CLI-006.5
def test_skip_specs_change(project):
    run_json("new", "tidy-up", "--no-branch")
    code, data = run_json("skip-specs", "--change", "tidy-up")
    assert code == 0 and data["skipSpecs"] is True
    (project / ".specworks/changes/active/tidy-up/proposal.md").write_text("# P\n\n## Why\n\n## What Changes\n\n## Capabilities\n")
    code, data = run_json("status", "--change", "tidy-up")
    states = {a["id"]: a["status"] for a in data["artifacts"]}
    assert states["specs"] == "skipped" and states["tasks"] == "ready"
    code, data = run_json("skip-specs", "--change", "tidy-up", "--off")
    assert data["skipSpecs"] is False
