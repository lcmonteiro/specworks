import pytest

from support.cli import make_project, run_json


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


# @ac AC-FLOW-002.1
def test_instructions_for_refinement(project):
    run_json("new", "add-login", "--no-branch")
    code, data = run_json("instructions", "refinement", "--change", "add-login")
    assert code == 0
    assert data["outputPath"] == ".specworks/changes/active/add-login/refinement.md"
    assert "## Options" in data["template"]
    assert data["exists"] is False


# @ac AC-FLOW-002.4
def test_instructions_for_an_unknown_artifact_are_refused(project):
    run_json("new", "add-login", "--no-branch")
    code, data = run_json("instructions", "plan", "--change", "add-login")
    assert code == 1 and "unknown artifact 'plan'" in data["error"]
    assert "refinement, proposal, specs, design, tasks, traceability, review" in data["error"]

# @ac AC-FLOW-001.2
def test_status_marks_refinement_done_once_written(project):
    run_json("new", "add-login", "--no-branch")
    (project / ".specworks/changes/active/add-login/refinement.md").write_text("# Refinement\n")
    code, data = run_json("status", "--change", "add-login")
    states = {a["id"]: a["status"] for a in data["artifacts"]}
    assert states["refinement"] == "done"
