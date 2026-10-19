import json
import re

import pytest
from typer.testing import CliRunner

from samples import DELTA, LIVING, PROPOSAL, TASKS
from specworks.cli import app
from specworks.specs.specfile import ac_parent, find_ids, id_prefix, living_problems, parse_spec
from specworks.specs.tasks import parse_tasks
from specworks.specs.trace import glob_match, is_test_file

runner = CliRunner()


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


@pytest.mark.parametrize(
    "fence",
    [
        "~~~\n### Requirement: REQ-X-002 B\n~~~\n",  # tildes
        "````\n```\n### Requirement: REQ-X-002 B\n```\n````\n",  # a shorter fence inside a longer one
        "~~~\n```\n### Requirement: REQ-X-002 B\n~~~\n",  # backticks do not close a tilde fence
    ],
)
def test_parse_ignores_headers_inside_any_code_fence(fence):
    doc = parse_spec("## ADDED Requirements\n### Requirement: REQ-X-001 A\nSHALL x\n" + fence + "### Requirement: REQ-X-003 C\nSHALL y\n")
    assert [r.id for r in doc.requirements] == ["REQ-X-001", "REQ-X-003"]


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


def test_proposal_section_in_a_code_fence_does_not_count(change):
    (change / "proposal.md").write_text(PROPOSAL.replace("## Why\nUsers get locked out.\n", "```\n## Why\n```\n"))
    code, data = run_json("check", "--change", "add-password-reset")
    assert "missing section '## Why'" in errors(data)


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
        ("REQ-AUTH-003 Password reset", "REQ-AUTH-003", "REQ-AUTH-003 has no title"),
        ("#### Scenario: AC-AUTH-003.2 Expired link", "#### Scenario: Expired link", "scenario header must be '#### Scenario: AC-AUTH-003.<n> <title>'"),
        ("## MODIFIED Requirements", "## Requirements", "uses '## ADDED/MODIFIED/REMOVED Requirements', not '## Requirements'"),
    ],
)
def test_delta_errors(change, old, new, message):
    replace_delta(change, old, new)
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 1
    assert any(message in m for m in errors(data)), errors(data)


def test_requirement_id_used_twice(change):
    replace_delta(change, "REQ-AUTH-002 Lockout after failures", "REQ-AUTH-003 Lockout after failures")
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 1 and any("REQ-AUTH-003 is used twice" in m for m in errors(data)), errors(data)


def test_delta_without_requirements(change):
    (change / "specs/user-auth/spec.md").write_text("# Spec Delta: user-auth\n\nNothing yet.\n")
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 1 and any(m.startswith("no requirements; add '## ADDED Requirements'") for m in errors(data)), errors(data)


def test_long_description_is_a_warning(change):
    replace_delta(change, "valid for 30 minutes.", "valid for 30 minutes." + " Really." * 200)
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 0 and any("REQ-AUTH-003: description is long" in i["message"] for i in data["issues"] if i["level"] == "warning")


def test_tasks_without_any_task(change):
    (change / "tasks.md").write_text("# Tasks\n\nTo do.\n")
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 1 and any(m.startswith("no tasks;") for m in errors(data)), errors(data)


def test_skip_specs_with_delta_specs(change):
    run_json("skip-specs", "--change", "add-password-reset")
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 1 and "skip_specs is set but the change has delta specs" in errors(data)


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


@pytest.mark.parametrize(
    "body, missing",
    [
        ("**Reason**: SSO only\n**Migration**: use SSO\n", None),
        ("**Reason:** SSO only\n- Migration: use SSO\n", None),  # bold around the colon, a bullet
        ("A reasonable cut; there is no migration path.\n", "Reason, Migration"),  # the words alone are not the fields
        ("**Reason**:\n**Migration**: use SSO\n", "Reason"),  # a label without its text
    ],
)
def test_removed_needs_reason_and_migration_lines(change, body, missing):
    replace_delta(change, "## MODIFIED", f"## REMOVED Requirements\n\n### Requirement: REQ-AUTH-001 Password login\n{body}\n## MODIFIED")
    code, data = run_json("check", "--change", "add-password-reset")
    found = [m for m in errors(data) if "REQ-AUTH-001: a REMOVED requirement needs" in m]
    if missing is None:
        assert found == []
    else:
        assert len(found) == 1 and f"(missing: {missing})" in found[0]


def test_new_capability_only_adds_and_needs_purpose(change):
    path = change / "specs/audit-log/spec.md"
    path.parent.mkdir()
    path.write_text("## MODIFIED Requirements\n\n### Requirement: REQ-AUDIT-LOG-001 Log\nThe system SHALL log.\n")
    code, data = run_json("check", "--change", "add-password-reset")
    assert any("has no living spec yet" in m for m in errors(data))
    assert any("add '## Purpose'" in i["message"] for i in data["issues"] if i["level"] == "warning")


def test_a_new_capability_that_is_not_registered_is_a_warning(change):
    path = change / "specs/audit-log/spec.md"
    path.parent.mkdir()
    path.write_text("## Purpose\nAudit.\n\n## ADDED Requirements\n\n### Requirement: REQ-AUDIT-LOG-001 Log\nThe system SHALL log.\n\n"
                    "#### Scenario: AC-AUDIT-LOG-001.1 Logged\n- **WHEN** x\n- **THEN** y\n")
    code, data = run_json("check", "--change", "add-password-reset")
    assert any(
        "new capability audit-log is not registered; register it before closing: specworks capability add audit-log --path <code path>"
        == i["message"] for i in data["issues"] if i["level"] == "warning"
    )


def test_delta_under_unknown_module(change):
    path = change / "specs/nope/thing/spec.md"
    path.parent.mkdir(parents=True)
    path.write_text("## ADDED Requirements\n")
    code, data = run_json("check", "--change", "add-password-reset")
    assert any("'nope' in specs/nope/thing/spec.md is not a module" in m for m in errors(data))


def started(project, name, created):
    meta = project / "spec/changes" / name / ".change.yaml"
    meta.write_text(re.sub(r"(?m)^created: .*$", f"created: '{created}'", meta.read_text()))


def warnings(data):
    return [i["message"] for i in data["issues"] if i["level"] == "warning"]


def test_id_clash_is_an_error_only_in_the_change_that_started_later(change, project):
    run_json("new", "other-change")
    other = project / "spec/changes/other-change/specs/user-auth"
    other.mkdir(parents=True)
    (other / "spec.md").write_text(DELTA)
    started(project, "add-password-reset", "2026-10-17T09:00:00")
    started(project, "other-change", "2026-10-17T10:00:00")
    code, data = run_json("check", "--change", "other-change")
    assert any("REQ-AUTH-003 is also added by change add-password-reset, which started first; take the next free ID" in m for m in errors(data))
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 0 and not any("other-change" in m for m in errors(data))
    assert any("REQ-AUTH-003 is also added by change other-change, which started later" in m for m in warnings(data))


def test_changes_started_on_the_same_day_without_a_time_are_ordered_by_name(change, project):
    run_json("new", "other-change")
    other = project / "spec/changes/other-change/specs/user-auth"
    other.mkdir(parents=True)
    (other / "spec.md").write_text(DELTA)
    started(project, "add-password-reset", "2026-10-17")
    started(project, "other-change", "2026-10-17")
    assert run_json("check", "--change", "add-password-reset")[0] == 0
    assert run_json("check", "--change", "other-change")[0] == 1


# @ac AC-PROJ-010.1
def test_a_new_change_records_when_it_started(project):
    run_json("new", "other-change")
    meta = (project / "spec/changes/other-change/.change.yaml").read_text()
    assert re.search(r"(?m)^created: '\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d'$", meta), meta


@pytest.mark.parametrize(
    "other_delta",
    [
        "## MODIFIED Requirements\n\n### Requirement: REQ-AUTH-002 Lockout\nThe system SHALL lock after 10 failures.\n\n"
        "#### Scenario: AC-AUTH-002.1 Tenth failure\n- **WHEN** the tenth wrong password is submitted\n- **THEN** the account is locked\n",
        "## REMOVED Requirements\n\n### Requirement: REQ-AUTH-002 Lockout\n**Reason**: SSO only\n**Migration**: none\n",
    ],
    ids=["modified", "removed"],
)
def test_two_changes_editing_one_requirement_do_not_block_each_other(change, project, other_delta):
    run_json("new", "other-change")
    other = project / "spec/changes/other-change/specs/user-auth"
    other.mkdir(parents=True)
    (other / "spec.md").write_text(other_delta)
    started(project, "add-password-reset", "2026-10-17T09:00:00")
    started(project, "other-change", "2026-10-17T10:00:00")
    code, data = run_json("check", "--change", "other-change")
    assert code == 1
    assert any("REQ-AUTH-002 is also MODIFIED or REMOVED by change add-password-reset, which started first; close it first" in m for m in errors(data))
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 0, errors(data)
    assert any("REQ-AUTH-002 is also MODIFIED or REMOVED by change other-change, which started later" in m for m in warnings(data))


BROKEN_LIVING = """
### Requirement: REQ-AUTH-002 Lockout (copy)
The system SHALL lock again.

#### Scenario: AC-AUTH-002.1 Copied
- **WHEN** x
- **THEN** y

### Requirement: Search by title
The system SHALL search.
"""


def test_check_warns_about_a_broken_living_spec(change, project):
    living = project / "src/auth/docs/spec.md"
    living.write_text(living.read_text() + BROKEN_LIVING)
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 0
    found = [i for i in data["issues"] if i["file"] == "src/auth/docs/spec.md"]
    assert {i["level"] for i in found} == {"warning"}
    messages = " | ".join(i["message"] for i in found)
    assert "living spec of user-auth: REQ-AUTH-002 is used twice" in messages and "fix it before closing" in messages
    assert "AC-AUTH-002.1 is used twice" in messages and "requirement header has no 'REQ-<prefix>-NNN' ID" in messages


@pytest.mark.parametrize(
    "text, problem",
    [
        ("## Requirements\n\n### Requirement: REQ-A-001 X\nThe system does x.\n\n#### Scenario: AC-A-001.1 Y\n- **WHEN** a\n- **THEN** b\n",
         "REQ-A-001: state the requirement with SHALL or MUST"),
        ("## Requirements\n\n### Requirement: REQ-A-001 X\nThe system SHALL x.\n", "REQ-A-001 has no '#### Scenario: AC-...' (acceptance criterion)"),
        ("## Requirements\n\n### Requirement: REQ-A-001 X\nThe system SHALL x.\n\n#### Scenario: no id\n- **WHEN** a\n- **THEN** b\n",
         "scenario of REQ-A-001 has no 'AC-<prefix>-NNN.<n>' ID"),
        ("## Requirements\n\n### Requirement: REQ-A-001 X\nThe system SHALL x.\n\n#### Scenario: AC-A-002.1 Y\n- **WHEN** a\n- **THEN** b\n",
         "AC-A-002.1 is under REQ-A-001"),
        ("## ADDED Requirements\n\n### Requirement: REQ-A-001 X\nThe system SHALL x.\n\n#### Scenario: AC-A-001.1 Y\n- **WHEN** a\n- **THEN** b\n",
         "requirement outside '## Requirements'"),
    ],
    ids=["no-shall", "no-scenario", "scenario-without-id", "scenario-under-another", "delta-section"],
)
def test_living_problems(text, problem):
    assert [message for _, message in living_problems(parse_spec(text))] == [problem]


def test_a_valid_living_spec_has_no_problems():
    assert living_problems(parse_spec(LIVING)) == []


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
    (project / "tests/test_reset.py").write_text("# @ac AC-AUTH-003.1\ndef test_request(): ...\n")  # specworks: ignore-tags
    (project / "src/auth/reset.py").write_text("def reset():  # @req REQ-AUTH-003\n    ...\n")  # specworks: ignore-tags
    (project / "src/auth/lockout.go").write_text("// @req REQ-AUTH-002\n// @req REQ-AUTH-077\n")  # specworks: ignore-tags
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
    (project / ".venv/x_test.py").write_text("# @ac AC-AUTH-003.1\n")  # specworks: ignore-tags
    (change / "notes_test.py").write_text("# @ac AC-AUTH-003.1\n")  # specworks: ignore-tags
    code, data = run_json("trace", "--change", "add-password-reset")
    assert {r["ac"]: r for r in data["rows"]}["AC-AUTH-003.1"]["tests"] == []


def test_trace_does_not_count_tags_quoted_in_docs(change, project):
    (project / "NOTES.md").write_text("TODO: implement `@req REQ-AUTH-003`\n")  # specworks: ignore-tags
    (project / "tests").mkdir()
    (project / "tests/README.txt").write_text("covers @ac AC-AUTH-003.1\n")  # specworks: ignore-tags
    (project / "tests/reset.feature").write_text("# @ac AC-AUTH-003.2\nScenario: expired link\n")  # specworks: ignore-tags
    code, data = run_json("trace", "--change", "add-password-reset")
    rows = {r["ac"]: r for r in data["rows"]}
    assert rows["AC-AUTH-003.1"]["code"] == [] and rows["AC-AUTH-003.1"]["tests"] == []
    assert rows["AC-AUTH-003.2"]["tests"] == ["tests/reset.feature:1"]  # non-code tests still count
    assert "REQ-AUTH-003" in data["gaps"]["reqWithoutCode"]


def test_globs_that_name_docs_scan_them(change, project):
    cfg = project / "spec.yml"
    cfg.write_text(cfg.read_text().replace("source_globs: []", 'source_globs: ["docs/*"]'))
    (project / "docs").mkdir()
    (project / "docs/impl.md").write_text("@req REQ-AUTH-003\n")  # specworks: ignore-tags
    code, data = run_json("trace", "--change", "add-password-reset")
    assert {r["ac"]: r for r in data["rows"]}["AC-AUTH-003.1"]["code"] == ["docs/impl.md:1"]


def test_trace_respects_test_globs(change, project):
    cfg = project / "spec.yml"
    cfg.write_text(cfg.read_text().replace("test_globs: []", 'test_globs: ["qa/*.py"]'))
    (project / "qa").mkdir()
    (project / "qa/reset_checks.py").write_text("# @ac AC-AUTH-003.2\n")  # specworks: ignore-tags
    code, data = run_json("trace", "--change", "add-password-reset")
    assert {r["ac"]: r for r in data["rows"]}["AC-AUTH-003.2"]["tests"] == ["qa/reset_checks.py:1"]


def test_tags_of_a_capability_with_a_longer_prefix_are_not_unknown(change, project):
    # The change touches AUTH; REQ-AUTH-ADMIN-001 belongs to another capability (prefix AUTH-ADMIN).
    run_json("capability", "add", "auth-admin", "--path", "src/admin", "--prefix", "AUTH-ADMIN")
    (project / "src/admin").mkdir(exist_ok=True)
    (project / "src/admin/users.py").write_text("# @req REQ-AUTH-ADMIN-001\n# @req REQ-AUTH-078\n")  # specworks: ignore-tags
    code, data = run_json("trace", "--change", "add-password-reset")
    assert data["unknownTags"] == [{"id": "REQ-AUTH-078", "where": "src/admin/users.py:2"}]


def test_a_tag_with_a_prefix_no_capability_uses_is_unknown(change, project):
    (project / "tests").mkdir()
    (project / "tests/test_reset.py").write_text("# @ac AC-AUHT-003.1\n# @req REQ-AUTH\n")  # specworks: ignore-tags
    code, data = run_json("trace", "--change", "add-password-reset")
    assert data["unknownTags"] == [
        {"id": "AC-AUHT-003.1", "where": "tests/test_reset.py:1", "hint": "no capability uses the prefix AUHT; did you mean AUTH?"},
        {"id": "REQ-AUTH", "where": "tests/test_reset.py:2", "hint": "not a REQ-<prefix>-NNN or AC-<prefix>-NNN.<n> ID"},
    ]


def test_tags_of_another_active_change_are_not_unknown(change, project):
    # other-change adds REQ-AUTH-004 to the same capability and a new, not yet registered one.
    run_json("new", "other-change")
    other = project / "spec/changes/other-change/specs"
    (other / "user-auth").mkdir(parents=True)
    (other / "user-auth/spec.md").write_text(DELTA.replace("REQ-AUTH-003", "REQ-AUTH-004").replace("AC-AUTH-003", "AC-AUTH-004"))
    (other / "audit-log").mkdir()
    (other / "audit-log/spec.md").write_text(
        "## Purpose\nAudit.\n\n## ADDED Requirements\n\n### Requirement: REQ-AUDIT-LOG-001 Log\nThe system SHALL log.\n\n"
        "#### Scenario: AC-AUDIT-LOG-001.1 Logged\n- **WHEN** x\n- **THEN** y\n"
    )
    (project / "tests").mkdir()
    (project / "tests/test_other.py").write_text("# @ac AC-AUTH-004.1\n# @ac AC-AUDIT-LOG-001.1\n# @ac AC-AUTH-005.1\n")  # specworks: ignore-tags
    code, data = run_json("trace", "--change", "add-password-reset")
    assert data["unknownTags"] == [{"id": "AC-AUTH-005.1", "where": "tests/test_other.py:3"}]


def test_a_broken_delta_of_another_change_does_not_break_this_ones_trace(change, project):
    run_json("new", "other-change")
    bad = project / "spec/changes/other-change/specs/nope/thing"
    bad.mkdir(parents=True)
    (bad / "spec.md").write_text("## ADDED Requirements\n")
    code, data = run_json("trace", "--change", "add-password-reset")
    assert code == 0 and data["unknownTags"] == []


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


def test_test_globs_do_not_hide_source_tags(change, project):
    cfg = project / "spec.yml"
    cfg.write_text(cfg.read_text().replace("test_globs: []", 'test_globs: ["qa/*.py"]'))
    (project / "qa").mkdir()
    (project / "qa/reset_checks.py").write_text("# @ac AC-AUTH-003.2\n")  # specworks: ignore-tags
    (project / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\n")  # specworks: ignore-tags
    code, data = run_json("trace", "--change", "add-password-reset")
    rows = {r["ac"]: r for r in data["rows"]}
    assert rows["AC-AUTH-003.2"]["tests"] == ["qa/reset_checks.py:1"]
    assert rows["AC-AUTH-003.2"]["code"] == ["src/auth/reset.py:1"]


def test_source_globs_limit_the_other_files_but_not_tests(change, project):
    cfg = project / "spec.yml"
    cfg.write_text(cfg.read_text().replace("source_globs: []", 'source_globs: ["src/**"]'))
    (project / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\n")  # specworks: ignore-tags
    (project / "scripts").mkdir()
    (project / "scripts/tool.py").write_text("# @req REQ-AUTH-003\n")  # specworks: ignore-tags
    (project / "tests").mkdir()
    (project / "tests/test_reset.py").write_text("# @ac AC-AUTH-003.1\n")  # specworks: ignore-tags
    code, data = run_json("trace", "--change", "add-password-reset")
    rows = {r["ac"]: r for r in data["rows"]}
    assert rows["AC-AUTH-003.1"]["code"] == ["src/auth/reset.py:1"]
    assert rows["AC-AUTH-003.1"]["tests"] == ["tests/test_reset.py:1"]


# @ac AC-FLOW-001.3, AC-CLI-006.5
def test_skip_specs_change(project):
    run_json("new", "tidy-up")
    code, data = run_json("skip-specs", "--change", "tidy-up")
    assert code == 0 and data["skipSpecs"] is True
    (project / "spec/changes/tidy-up/proposal.md").write_text("# P\n\n## Why\n\n## What Changes\n\n## Capabilities\n")
    code, data = run_json("status", "--change", "tidy-up")
    states = {a["id"]: a["status"] for a in data["artifacts"]}
    assert states["specs"] == "skipped" and states["tasks"] == "ready"
    code, data = run_json("skip-specs", "--change", "tidy-up", "--off")
    assert data["skipSpecs"] is False


# @ac AC-PROJ-005.1
def test_two_capabilities_with_one_prefix_is_an_error(project):
    cfg = project / "spec.yml"
    cfg.write_text(cfg.read_text().replace("    prefix: AUTH\n", "    prefix: AUTH\n  login:\n    path: src/login\n    prefix: AUTH\n", 1))
    code, data = run_json("spec", "list")
    assert code == 1 and "user-auth and login both use the ID prefix AUTH" in data["error"]


def test_new_capability_may_not_take_a_prefix_in_use(change):
    path = change / "specs/auth"
    path.mkdir(parents=True)
    (path / "spec.md").write_text("## Purpose\n\nAuth.\n\n" + DELTA.split("## MODIFIED")[0].replace("REQ-AUTH-003", "REQ-AUTH-009").replace("AC-AUTH-003", "AC-AUTH-009"))
    code, data = run_json("check", "--change", "add-password-reset")
    messages = [i["message"] for i in data["issues"]]
    assert code == 1 and any("new capability auth would use the ID prefix AUTH, already used by user-auth" in m for m in messages), messages


def test_tasks_in_a_code_fence_are_examples_not_tasks():
    text = "## 1. Reset\n\n- [ ] 1.1 Add reset (REQ-AUTH-003)\n\n```markdown\n- [ ] 9.9 an example task\n- [x] bad example\n```\n"
    tasks, problems = parse_tasks(text)
    assert [t.num for t in tasks] == ["1.1"] and problems == []


@pytest.mark.parametrize(
    "rel, pattern, expected",
    [
        ("tests/test_a.py", "tests/**/*.py", True),  # ** spans zero folders too
        ("tests/unit/test_a.py", "tests/**/*.py", True),
        ("test_a.py", "**/test_*.py", True),
        ("a/b/test_a.py", "**/test_*.py", True),
        ("src/x.py", "src/*.py", True),
        ("src/a/x.py", "src/*.py", False),  # * stays within one folder
        ("src/a/x.py", "src/**", True),
        ("qa/x1.py", "qa/x?.py", True),
        ("qa/x/1.py", "qa/x?1.py", False),
    ],
)
def test_globs_follow_folder_aware_rules(rel, pattern, expected):
    assert glob_match(rel, pattern) is expected


def test_one_tag_may_list_several_ids(change, project):
    (project / "tests").mkdir()
    (project / "tests/test_reset.py").write_text("# @ac AC-AUTH-003.1, AC-AUTH-003.2\n")  # specworks: ignore-tags
    code, data = run_json("trace", "--change", "add-password-reset")
    rows = {r["ac"]: r for r in data["rows"]}
    assert rows["AC-AUTH-003.1"]["tests"] == rows["AC-AUTH-003.2"]["tests"] == ["tests/test_reset.py:1"]


def test_html_comments_are_not_spec_content():
    text = "## Purpose\n\n<!-- hint -->\n\n## ADDED Requirements\n\n<!--\n### Requirement: REQ-AUTH-009 Idea\n-->\n### Requirement: REQ-AUTH-010 Real\nThe system SHALL x.\n"
    doc = parse_spec(text)
    assert doc.purpose == ""
    assert [(r.id, r.line) for r in doc.requirements] == [("REQ-AUTH-010", 10)]  # line numbers are kept


def check_warnings(ref="add-password-reset"):
    _, data = run_json("check", "--change", ref)
    return [i["message"] for i in data["issues"] if i["level"] == "warning"]


@pytest.mark.parametrize("closed, warned", [("2999-01-01", True), ("2000-01-01", False)])
def test_requirement_modified_by_a_later_close_is_warned(change, project, closed, warned):
    # Another change closed after this one started: this MODIFIED block may predate its edits.
    history = f"# Requirements: user-auth\n\n## History\n\n- {closed} `stricter-lockout`: MODIFIED REQ-AUTH-002\n"
    (project / "src/auth/docs/requirements.md").write_text(history)
    found = [w for w in check_warnings() if w.startswith("REQ-AUTH-002 was MODIFIED by stricter-lockout")]
    assert bool(found) is warned


def test_modified_block_dropping_a_criterion_is_warned(change, project):
    delta = change / "specs/user-auth/spec.md"
    delta.write_text(DELTA.replace("AC-AUTH-002.1 Third failure", "AC-AUTH-002.2 Third failure"))
    assert any(w.startswith("REQ-AUTH-002: this MODIFIED block drops AC-AUTH-002.1") for w in check_warnings())
    # Gates show `specworks check` warnings without blocking on them.
    _, data = run_json("gate", "specify", "--change", "add-password-reset")
    row = next(c for c in data["checks"] if c["name"] == "specworks check has no warnings")
    assert row["ok"] is False and row["blocking"] is False


# @ac AC-PROJ-015.1
def test_a_file_that_is_not_utf8_is_a_clear_error(change):
    (change / "specs/user-auth/spec.md").write_bytes(DELTA.encode().replace(b"single-use", b"single\xe9use"))
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 1 and "is not UTF-8 text" in data["error"] and "spec.md" in data["error"]


# --- ignore markers ----------------------------------------------------------
# Sample tags below are fixture content: each line carries the marker, or quotes one.


def trace_rows(project, files):
    for name, text in files.items():
        (project / name).parent.mkdir(parents=True, exist_ok=True)
        (project / name).write_text(text)
    code, data = run_json("trace", "--change", "add-password-reset")
    return {r["ac"]: r for r in data["rows"]}, data


# @ac AC-SPECS-001.1
def test_a_marked_line_is_skipped_and_the_next_is_not(change, project):
    rows, _ = trace_rows(project, {"tests/test_reset.py": "# @ac AC-AUTH-003.1  # specworks: ignore-tags\n# @ac AC-AUTH-003.2\n"})  # specworks: ignore-tags
    assert rows["AC-AUTH-003.1"]["tests"] == [] and rows["AC-AUTH-003.2"]["tests"] == ["tests/test_reset.py:2"]


# @ac AC-SPECS-001.2
def test_the_line_marker_works_in_any_comment_syntax(change, project):
    rows, data = trace_rows(project, {"src/auth/lockout.go": "x := 1 // @req REQ-AUTH-002 @req REQ-AUTH-077 // specworks: ignore-tags\n"})
    assert rows["AC-AUTH-002.1"]["code"] == [] and data["unknownTags"] == []


# @ac AC-SPECS-002.1
def test_the_lines_of_a_block_are_skipped(change, project):
    rows, data = trace_rows(project, {
        "tests/test_reset.py": "# @ac AC-AUTH-003.1\n# specworks: ignore-tags-start\n# @ac AC-AUTH-003.2\n# @req REQ-AUTH-077\n"  # specworks: ignore-tags
                               "# specworks: ignore-tags-end\n# @ac AC-AUTH-002.1\n",  # specworks: ignore-tags
        "src/auth/lockout.go": "/* specworks: ignore-tags-start */\n// @req REQ-AUTH-002\n/* specworks: ignore-tags-end */\n",  # specworks: ignore-tags
    })
    assert rows["AC-AUTH-003.1"]["tests"] == ["tests/test_reset.py:1"] and rows["AC-AUTH-003.2"]["tests"] == []
    assert rows["AC-AUTH-002.1"]["tests"] == ["tests/test_reset.py:6"] and rows["AC-AUTH-002.1"]["code"] == []
    assert data["unknownTags"] == []


# @ac AC-SPECS-002.2
def test_a_block_with_no_end_stops_at_the_end_of_its_file(change, project):
    rows, _ = trace_rows(project, {
        "tests/test_a.py": "# specworks: ignore-tags-start\n# @ac AC-AUTH-003.1\n",  # specworks: ignore-tags
        "tests/test_b.py": "# @ac AC-AUTH-003.2\n",  # specworks: ignore-tags
    })
    assert rows["AC-AUTH-003.1"]["tests"] == [] and rows["AC-AUTH-003.2"]["tests"] == ["tests/test_b.py:1"]


# @ac AC-SPECS-002.3
def test_a_marker_quoted_in_prose_opens_no_block(change, project):
    rows, _ = trace_rows(project, {"tests/test_reset.py": "# Lines from specworks: ignore-tags-start are skipped\n# @ac AC-AUTH-003.1\n"})  # specworks: ignore-tags
    assert rows["AC-AUTH-003.1"]["tests"] == ["tests/test_reset.py:2"]


# @ac AC-SPECS-002.4
def test_an_end_with_no_start_is_ignored(change, project):
    rows, _ = trace_rows(project, {"tests/test_reset.py": "# specworks: ignore-tags-end\n# @ac AC-AUTH-003.1\n"})  # specworks: ignore-tags
    assert rows["AC-AUTH-003.1"]["tests"] == ["tests/test_reset.py:2"]


# @ac AC-SPECS-003.1
def test_an_ignored_tag_is_not_unknown(change, project):
    _, data = trace_rows(project, {"tests/test_reset.py": "# @ac AC-AUHT-003.1  # specworks: ignore-tags\n"})
    assert data["unknownTags"] == []


# @ac AC-SPECS-003.2
def test_an_ignored_tag_is_not_coverage(change, project):
    _, data = trace_rows(project, {"tests/test_reset.py": "# @ac AC-AUTH-003.1  # specworks: ignore-tags\n"})
    assert "AC-AUTH-003.1" in data["gaps"]["acWithoutTests"]
