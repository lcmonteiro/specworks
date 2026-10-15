import json

import pytest
from typer.testing import CliRunner

from specworks.cli import app
from specworks.specs.specfile import ac_parent, find_ids, id_prefix, parse_spec
from specworks.specs.trace import is_test_file

runner = CliRunner()

LIVING = """\
# user-auth

## Purpose

Lets users prove who they are.

## Requirements

### Requirement: REQ-AUTH-001 Password login
The system SHALL let a user log in with email and password.

#### Scenario: AC-AUTH-001.1 Valid password
- **WHEN** a user submits a correct password
- **THEN** a session is created

### Requirement: REQ-AUTH-002 Lockout
The system SHALL lock an account after 5 failed attempts.

#### Scenario: AC-AUTH-002.1 Fifth failure
- **WHEN** the fifth wrong password is submitted
- **THEN** the account is locked
"""

DELTA = """\
# Spec Delta: user-auth

## ADDED Requirements

### Requirement: REQ-AUTH-003 Password reset
The system SHALL email a single-use reset link valid for 30 minutes.

#### Scenario: AC-AUTH-003.1 Request reset
- **WHEN** a user asks for a reset with a known email
- **THEN** a reset link is emailed

#### Scenario: AC-AUTH-003.2 Expired link
- **GIVEN** a link older than 30 minutes
- **WHEN** it is opened
- **THEN** the user is told it expired

## MODIFIED Requirements

### Requirement: REQ-AUTH-002 Lockout after failures
The system SHALL lock an account after 3 failed attempts.

#### Scenario: AC-AUTH-002.1 Third failure
- **WHEN** the third wrong password is submitted
- **THEN** the account is locked
"""

PROPOSAL = """\
# Proposal: add-password-reset

## Why
Users get locked out.

## What Changes
- Password reset by email

## Capabilities
### Modified Capabilities
- `user-auth`: reset + stricter lockout

## Impact
auth service
"""

TASKS = """\
# Tasks

## 1. Reset

- [ ] 1.1 Write failing tests for AC-AUTH-003.1 and AC-AUTH-003.2; verify they fail
- [ ] 1.2 Implement reset links (REQ-AUTH-003); verify 1.1 passes

## 2. Lockout

- [x] 2.1 Lower the lockout threshold (REQ-AUTH-002); verify AC-AUTH-002.1 test passes
"""


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        pytest.fail(result.output)


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["init", "--dir", "spec", "--no-skills"]).exit_code == 0
    cfg = tmp_path / "spec.yml"
    cfg.write_text(
        cfg.read_text().replace(
            "capabilities: {}", "capabilities:\n  user-auth:\n    path: src/auth\n    prefix: AUTH\n  billing:\n    path: src/billing"
        )
    )
    (tmp_path / "src/auth/docs").mkdir(parents=True)
    (tmp_path / "src/auth/docs/spec.md").write_text(LIVING)
    run_json("new", "add-password-reset")
    return tmp_path


@pytest.fixture
def change(project):
    path = project / "spec/changes/add-password-reset"
    (path / "proposal.md").write_text(PROPOSAL)
    (path / "specs/user-auth").mkdir(parents=True)
    (path / "specs/user-auth/spec.md").write_text(DELTA)
    (path / "tasks.md").write_text(TASKS)
    return path


def errors(data):
    return [i["message"] for i in data["issues"] if i["level"] == "error"]


# --- parser ------------------------------------------------------------------


def test_parse_living_spec():
    doc = parse_spec(LIVING)
    assert doc.purpose == "Lets users prove who they are."
    assert [(r.id, r.title, r.section) for r in doc.requirements] == [
        ("REQ-AUTH-001", "Password login", "Requirements"),
        ("REQ-AUTH-002", "Lockout", "Requirements"),
    ]
    assert [s.id for s in doc.requirements[0].scenarios] == ["AC-AUTH-001.1"]


def test_parse_ignores_headers_inside_code_fences():
    doc = parse_spec("## ADDED Requirements\n### Requirement: REQ-X-001 A\nSHALL x\n```\n### Requirement: REQ-X-002 B\n```\n")
    assert [r.id for r in doc.requirements] == ["REQ-X-001"]


def test_ids_helpers():
    assert find_ids("covers AC-BILLING-INVOICES-001.2 and REQ-AUTH-003.") == ["AC-BILLING-INVOICES-001.2", "REQ-AUTH-003"]
    assert ac_parent("AC-BILLING-INVOICES-001.2") == "REQ-BILLING-INVOICES-001"
    assert id_prefix("REQ-BILLING-INVOICES-001") == "BILLING-INVOICES" == id_prefix("AC-BILLING-INVOICES-001.2")
    assert id_prefix("REQ-V2-001") == "V2" and id_prefix("REQ-AUTH") is None and id_prefix("nope") is None


def test_ids_with_an_all_digit_prefix_segment():
    assert find_ids("task (REQ-OAUTH-2-001, AC-OAUTH-2-001.1)") == ["REQ-OAUTH-2-001", "AC-OAUTH-2-001.1"]
    assert id_prefix("REQ-OAUTH-2-001") == "OAUTH-2" and ac_parent("AC-OAUTH-2-001.1") == "REQ-OAUTH-2-001"
    doc = parse_spec("## ADDED Requirements\n\n### Requirement: REQ-OAUTH-2-001 Login\nThe system SHALL x.\n")
    assert (doc.requirements[0].id, doc.requirements[0].title) == ("REQ-OAUTH-2-001", "Login")


def test_change_for_a_capability_with_an_all_digit_prefix_segment(project):
    run_json("capability", "add", "oauth-2", "--path", "src/oauth")
    code, data = run_json("spec", "show", "oauth-2")
    assert data["prefix"] == "OAUTH-2" and data["nextId"] == "REQ-OAUTH-2-001"
    path = project / "spec/changes/add-password-reset"
    (path / "proposal.md").write_text(PROPOSAL)
    (path / "specs/oauth-2").mkdir(parents=True)
    (path / "specs/oauth-2/spec.md").write_text(
        "## Purpose\n\nOAuth 2 login.\n\n## ADDED Requirements\n\n### Requirement: REQ-OAUTH-2-001 Login\nThe system SHALL log in.\n\n"
        "#### Scenario: AC-OAUTH-2-001.1 Valid token\n- **WHEN** a valid token is sent\n- **THEN** the user is logged in\n"
    )
    (path / "tasks.md").write_text("## 1. Login\n\n- [ ] 1.1 Implement login (REQ-OAUTH-2-001, AC-OAUTH-2-001.1); verify the test passes\n")
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 0, errors(data)


def test_requirement_markdown_round_trips():
    req = parse_spec(DELTA).requirements[0]
    assert parse_spec("## ADDED Requirements\n" + req.markdown()).requirements[0].scenarios[1].id == "AC-AUTH-003.2"


# --- spec show / context -----------------------------------------------------


def test_spec_show_existing_capability(project):
    code, data = run_json("spec", "show", "user-auth")
    assert code == 0
    assert data["prefix"] == "AUTH" and data["nextId"] == "REQ-AUTH-003"
    assert data["deltaPath"] == "specs/user-auth/spec.md"
    assert data["livingSpec"] == "src/auth/docs/spec.md"
    assert [r["id"] for r in data["requirements"]] == ["REQ-AUTH-001", "REQ-AUTH-002"]


def test_spec_show_new_capability_derives_prefix(project):
    code, data = run_json("spec", "show", "audit-log")
    assert data["new"] is True and data["prefix"] == "AUDIT-LOG" and data["nextId"] == "REQ-AUDIT-LOG-001"


def test_next_id_counts_ids_added_by_active_changes(change):
    code, data = run_json("spec", "show", "user-auth")
    assert data["nextId"] == "REQ-AUTH-004"


REMOVED_HISTORY = "# Requirements: user-auth\n\n## History\n\n- 2026-01-02 `drop-sso`: REMOVED REQ-AUTH-003, REQ-AUTH-005\n"


def test_next_id_skips_removed_requirements(project):
    (project / "src/auth/docs/requirements.md").write_text(REMOVED_HISTORY)
    code, data = run_json("spec", "show", "user-auth")
    assert data["nextId"] == "REQ-AUTH-006"


def test_a_removed_id_cannot_be_added_again(change, project):
    (project / "src/auth/docs/requirements.md").write_text(REMOVED_HISTORY)
    code, data = run_json("check", "--change", "add-password-reset")
    assert any("REQ-AUTH-003 was removed from user-auth" in m and "never reused" in m for m in errors(data))


def test_spec_show_in_module_uses_module_path_and_prefix(project, monkeypatch):
    runner.invoke(app, ["module", "add", "services/pay"])
    cfg = project / "services/pay/spec.yml"
    cfg.write_text(cfg.read_text().replace("capabilities: {}", "capabilities:\n  refunds:\n    path: src/refunds"))
    code, data = run_json("spec", "show", "pay:refunds")
    assert data["prefix"] == "PAY-REFUNDS" and data["deltaPath"] == "specs/pay/refunds/spec.md"


def test_instructions_for_specs_list_capabilities(project):
    code, data = run_json("instructions", "specs", "--change", "add-password-reset")
    caps = {c["ref"]: c for c in data["capabilities"]}
    assert caps["user-auth"]["nextId"] == "REQ-AUTH-003"
    assert "REQ-<prefix>-NNN" in data["instruction"]


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
    }


# --- validate ----------------------------------------------------------------


def test_valid_change(change):
    code, data = run_json("check", "--change", "add-password-reset")
    assert errors(data) == []
    assert code == 0 and data["valid"] is True


def test_missing_proposal_and_specs(project):
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 1
    msgs = " | ".join(errors(data))
    assert "proposal.md is missing" in msgs and "no delta specs" in msgs


def replace_delta(change, old, new):
    path = change / "specs/user-auth/spec.md"
    assert old in path.read_text()
    path.write_text(path.read_text().replace(old, new))


@pytest.mark.parametrize(
    "old, new, message",
    [
        ("REQ-AUTH-003 Password reset", "REQ-AUTH-001 Password reset", "already exists in user-auth; use MODIFIED"),
        ("REQ-AUTH-003 Password reset", "REQ-BILL-003 Password reset", "use the prefix REQ-AUTH-"),
        ("REQ-AUTH-003 Password reset", "Password reset", "must be '### Requirement: REQ-AUTH-NNN <title>'"),
        ("The system SHALL email", "The system emails", "state the requirement with SHALL or MUST"),
        ("#### Scenario: AC-AUTH-003.2", "### Scenario: AC-AUTH-003.2", "exactly four hashes"),
        ("AC-AUTH-003.2 Expired", "AC-AUTH-002.2 Expired", "is under REQ-AUTH-003"),
        ("AC-AUTH-003.2 Expired", "AC-AUTH-003.1 Expired", "AC-AUTH-003.1 is used twice"),
        ("- **THEN** the user is told it expired", "- the user is told", "'- **WHEN** ...' / '- **THEN** ...'"),
        ("REQ-AUTH-002 Lockout after failures", "REQ-AUTH-009 Lockout after failures", "not in the living spec"),
    ],
)
def test_delta_errors(change, old, new, message):
    replace_delta(change, old, new)
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 1
    assert any(message in m for m in errors(data)), errors(data)


def test_requirement_without_scenario(change):
    replace_delta(
        change,
        "## MODIFIED Requirements",
        "### Requirement: REQ-AUTH-004 Audit\nThe system SHALL log resets.\n\n## MODIFIED Requirements",
    )
    code, data = run_json("check", "--change", "add-password-reset")
    assert any("REQ-AUTH-004 needs at least one" in m for m in errors(data))


def test_removed_needs_reason_and_migration(change):
    replace_delta(change, "## MODIFIED", "## REMOVED Requirements\n\n### Requirement: REQ-AUTH-001 Password login\n\n## MODIFIED")
    code, data = run_json("check", "--change", "add-password-reset")
    assert any("needs **Reason** and **Migration**" in m for m in errors(data))


def test_new_capability_only_adds_and_needs_purpose(change):
    path = change / "specs/audit-log/spec.md"
    path.parent.mkdir()
    path.write_text("## MODIFIED Requirements\n\n### Requirement: REQ-AUDIT-LOG-001 Log\nThe system SHALL log.\n")
    code, data = run_json("check", "--change", "add-password-reset")
    assert any("has no living spec yet" in m for m in errors(data))
    assert any("add '## Purpose'" in i["message"] for i in data["issues"] if i["level"] == "warning")


def test_delta_under_unknown_module(change):
    path = change / "specs/nope/thing/spec.md"
    path.parent.mkdir(parents=True)
    path.write_text("## ADDED Requirements\n")
    code, data = run_json("check", "--change", "add-password-reset")
    assert any("'nope' in specs/nope/thing/spec.md is not a module" in m for m in errors(data))


def test_id_clash_with_another_change(change, project):
    run_json("new", "other-change")
    other = project / "spec/changes/other-change/specs/user-auth"
    other.mkdir(parents=True)
    (other / "spec.md").write_text(DELTA)
    code, data = run_json("check", "--change", "add-password-reset")
    assert any("REQ-AUTH-003 is also added by change other-change" in m for m in errors(data))


@pytest.mark.parametrize(
    "other_delta",
    [
        "## MODIFIED Requirements\n\n### Requirement: REQ-AUTH-002 Lockout\nThe system SHALL lock after 10 failures.\n\n"
        "#### Scenario: AC-AUTH-002.1 Tenth failure\n- **WHEN** the tenth wrong password is submitted\n- **THEN** the account is locked\n",
        "## REMOVED Requirements\n\n### Requirement: REQ-AUTH-002 Lockout\n**Reason**: SSO only\n**Migration**: none\n",
    ],
    ids=["modified", "removed"],
)
def test_two_changes_cannot_edit_the_same_requirement(change, project, other_delta):
    run_json("new", "other-change")
    other = project / "spec/changes/other-change/specs/user-auth"
    other.mkdir(parents=True)
    (other / "spec.md").write_text(other_delta)
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 1
    assert any("REQ-AUTH-002 is also MODIFIED or REMOVED by change other-change; close one change first" in m for m in errors(data))
    code, data = run_json("check", "--change", "other-change")
    assert any("REQ-AUTH-002 is also MODIFIED or REMOVED by change add-password-reset" in m for m in errors(data))


def test_skip_specs(project):
    path = project / "spec/changes/add-password-reset"
    (path / "proposal.md").write_text(PROPOSAL)
    (path / ".change.yaml").write_text((path / ".change.yaml").read_text() + "skip_specs: true\n")
    code, data = run_json("check", "--change", "add-password-reset")
    assert errors(data) == [] and code == 0


def test_tasks_must_cover_every_acceptance_criterion(change):
    (change / "tasks.md").write_text(TASKS.replace("AC-AUTH-003.1 and AC-AUTH-003.2", "AC-AUTH-003.1").replace(" (REQ-AUTH-003)", ""))
    code, data = run_json("check", "--change", "add-password-reset")
    assert any("AC-AUTH-003.2 (user-auth) is not covered by any task" in m for m in errors(data))


def test_tasks_format_and_unknown_ids(change):
    (change / "tasks.md").write_text(TASKS + "- [ ] fix stuff\n- [ ] 3.1 Cover REQ-AUTH-042\n- [ ] 1.1 duplicate\n")
    code, data = run_json("check", "--change", "add-password-reset")
    msgs = " | ".join(errors(data))
    assert "task must be '- [ ] N.M description'" in msgs
    assert "refers to REQ-AUTH-042" in msgs
    assert "task 1.1 is numbered twice" in msgs


def test_tasks_not_written_is_only_a_warning(change):
    (change / "tasks.md").unlink()
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 0 and any("tasks.md is not written yet" in i["message"] for i in data["issues"])
    code, data = run_json("check", "--change", "add-password-reset", "--strict")
    assert code == 1


# --- trace -------------------------------------------------------------------


def test_trace_links_tasks_tests_and_code(change, project):
    (project / "tests").mkdir()
    (project / "tests/test_reset.py").write_text("# @ac AC-AUTH-003.1\ndef test_request(): ...\n")
    (project / "src/auth/reset.py").write_text("def reset():  # @req REQ-AUTH-003\n    ...\n")
    (project / "src/auth/lockout.go").write_text("// @req REQ-AUTH-002\n// @req REQ-AUTH-077\n")
    code, data = run_json("trace", "--change", "add-password-reset", "--write")
    assert code == 0
    rows = {r["ac"]: r for r in data["rows"]}
    assert rows["AC-AUTH-003.1"]["tasks"] == ["1.1", "1.2"]
    assert rows["AC-AUTH-003.1"]["tests"] == ["tests/test_reset.py:1"]
    assert rows["AC-AUTH-003.1"]["code"] == ["src/auth/reset.py:1"]
    assert rows["AC-AUTH-002.1"]["tasks"] == ["2.1"]
    assert data["gaps"]["acWithoutTests"] == ["AC-AUTH-003.2", "AC-AUTH-002.1"]
    assert data["gaps"]["reqWithoutCode"] == []
    assert data["unknownTags"] == [{"id": "REQ-AUTH-077", "where": "src/auth/lockout.go:2"}]
    text = (change / "traceability.md").read_text()
    assert "| user-auth | REQ-AUTH-003 Password reset (ADDED) | AC-AUTH-003.1 Request reset | 1.1, 1.2 |" in text
    assert "Acceptance criteria without a test (`@ac`): AC-AUTH-003.2, AC-AUTH-002.1" in text


def test_trace_skips_workflow_and_hidden_folders(change, project):
    (project / ".venv").mkdir()
    (project / ".venv/x_test.py").write_text("# @ac AC-AUTH-003.1\n")
    (change / "notes_test.py").write_text("# @ac AC-AUTH-003.1\n")
    code, data = run_json("trace", "--change", "add-password-reset")
    assert {r["ac"]: r for r in data["rows"]}["AC-AUTH-003.1"]["tests"] == []


def test_trace_does_not_count_tags_quoted_in_docs(change, project):
    (project / "NOTES.md").write_text("TODO: implement `@req REQ-AUTH-003`\n")
    (project / "tests").mkdir()
    (project / "tests/README.txt").write_text("covers @ac AC-AUTH-003.1\n")
    (project / "tests/reset.feature").write_text("# @ac AC-AUTH-003.2\nScenario: expired link\n")
    code, data = run_json("trace", "--change", "add-password-reset")
    rows = {r["ac"]: r for r in data["rows"]}
    assert rows["AC-AUTH-003.1"]["code"] == [] and rows["AC-AUTH-003.1"]["tests"] == []
    assert rows["AC-AUTH-003.2"]["tests"] == ["tests/reset.feature:1"]  # non-code tests still count
    assert "REQ-AUTH-003" in data["gaps"]["reqWithoutCode"]


def test_globs_that_name_docs_scan_them(change, project):
    cfg = project / "spec.yml"
    cfg.write_text(cfg.read_text().replace("source_globs: []", 'source_globs: ["docs/*"]'))
    (project / "docs").mkdir()
    (project / "docs/impl.md").write_text("@req REQ-AUTH-003\n")
    code, data = run_json("trace", "--change", "add-password-reset")
    assert {r["ac"]: r for r in data["rows"]}["AC-AUTH-003.1"]["code"] == ["docs/impl.md:1"]


def test_trace_respects_test_globs(change, project):
    cfg = project / "spec.yml"
    cfg.write_text(cfg.read_text().replace("test_globs: []", 'test_globs: ["qa/*.py"]'))
    (project / "qa").mkdir()
    (project / "qa/reset_checks.py").write_text("# @ac AC-AUTH-003.2\n")
    code, data = run_json("trace", "--change", "add-password-reset")
    assert {r["ac"]: r for r in data["rows"]}["AC-AUTH-003.2"]["tests"] == ["qa/reset_checks.py:1"]


def test_tags_of_a_capability_with_a_longer_prefix_are_not_unknown(change, project):
    # The change touches AUTH; REQ-AUTH-ADMIN-001 belongs to another capability (prefix AUTH-ADMIN).
    (project / "src/admin").mkdir()
    (project / "src/admin/users.py").write_text("# @req REQ-AUTH-ADMIN-001\n# @req REQ-AUTH-078\n")
    code, data = run_json("trace", "--change", "add-password-reset")
    assert data["unknownTags"] == [{"id": "REQ-AUTH-078", "where": "src/admin/users.py:2"}]


@pytest.mark.parametrize(
    "path, is_test",
    [
        ("tests/test_x.py", True),
        ("pkg/__tests__/x.js", True),
        ("spec/models/user_spec.rb", True),
        ("web/x.spec.ts", True),
        ("src/myapp/specs/check.py", False),  # a source package that happens to be called specs
        ("api/spec/openapi.py", False),
    ],
)
def test_test_file_detection(path, is_test):
    assert is_test_file(path, []) is is_test
