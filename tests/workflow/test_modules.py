import pytest

from support.modules import make_workspace, run_json


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    return make_workspace(tmp_path, monkeypatch)


# @ac AC-FLOW-002.2
def test_instructions_in_module_use_inherited_context(workspace):
    run_json("new", "add-refunds", "--module", "billing", "--no-branch")
    code, data = run_json("instructions", "refinement", "--change", "billing:add-refunds")
    assert data["outputPath"] == "services/billing/.specworks/changes/active/add-refunds/refinement.md"
    assert "Company-wide" in data["context"] and "Billing" in data["context"]
