import pytest

from samples import PROPOSAL
from support.propose import errors, make_project, run_json


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


def test_change_for_a_capability_with_an_all_digit_prefix_segment(project):
    run_json("capability", "add", "oauth-2", "--path", "src/oauth")
    code, data = run_json("spec", "show", "oauth-2")
    assert data["prefix"] == "OAUTH-2" and data["nextId"] == "REQ-OAUTH-2-001"
    path = project / ".specworks/changes/active/add-password-reset"
    (path / "proposal.md").write_text(PROPOSAL)
    (path / "specs/oauth-2").mkdir(parents=True)
    (path / "specs/oauth-2/spec.md").write_text(
        "## Purpose\n\nOAuth 2 login.\n\n## ADDED Requirements\n\n### Requirement: REQ-OAUTH-2-001 Login\nThe system SHALL log in.\n\n"
        "#### Scenario: AC-OAUTH-2-001.1 Valid token\n- **WHEN** a valid token is sent\n- **THEN** the user is logged in\n"
    )
    (path / "tasks.md").write_text("## 1. Login\n\n- [ ] 1.1 Implement login (REQ-OAUTH-2-001, AC-OAUTH-2-001.1); verify the test passes\n")
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 0, errors(data)
