"""
A capability's test folder, the scoped test command, and the review gate running only the touched capabilities' tests.
"""

import pytest

from helpers import on_a_branch, run_json
from support.capability_tests import add_billing_module, commands_block, make_log, new_project, runs, write

REF = "add-login-audit"
TESTS = "the test suite passes (commands.test)"
SCOPED = "the touched capabilities' tests pass (commands.test_scoped)"

DELTA_AUTH = """\
# Spec Delta: auth

## Purpose

Who logged in, and when.

## ADDED Requirements

### Requirement: REQ-AUTH-001 Login audit
The system SHALL record every login.

#### Scenario: AC-AUTH-001.1 Login recorded
- **WHEN** a user logs in
- **THEN** the login is recorded
"""

DELTA_INVOICES = """\
# Spec Delta: billing:invoices

## Purpose

Invoices sent to customers.

## ADDED Requirements

### Requirement: REQ-BILLING-INVOICES-001 Monthly invoice
The system SHALL send an invoice every month.

#### Scenario: AC-BILLING-INVOICES-001.1 Invoice sent
- **WHEN** a month ends
- **THEN** an invoice is sent
"""

PROPOSAL = f"""\
# Proposal: {REF}

## Why
Logins are not audited.

## What Changes
- Record every login

## Capabilities
### Modified Capabilities
- `auth`: login audit

## Impact
auth service
"""

TASKS = """\
# Tasks

## 1. Audit

- [x] 1.1 [test] Write failing tests for AC-AUTH-001.1; verify they fail
- [x] 1.2 [code] Record logins (REQ-AUTH-001); verify lint passes
"""

TASKS_INVOICES = TASKS + """
## 2. Invoices

- [x] 2.1 [test] Write failing tests for AC-BILLING-INVOICES-001.1; verify they fail
- [x] 2.2 [code] Send invoices (REQ-BILLING-INVOICES-001); verify lint passes
"""


def tag(kind, ids):
    """
    A tag line for a sample project's file, built here so this repo's own trace does not read it.
    """
    return f"# @{kind} {ids}\n"


@pytest.fixture
def log(tmp_path_factory):
    return make_log(tmp_path_factory)


AUTH_AND_BILLING = "  auth:\n    path: src/auth\n    prefix: AUTH\n  billing:\n    path: src/billing\n    prefix: BILL\n"


def make_project(root, monkeypatch, log, *, scoped=True, auth_folder=True, billing_fails=True):
    """
    Capabilities auth (src/auth) and billing (src/billing), each with a test folder under tests/, committed on main;
    on a feature branch, a change with a delta spec for auth, its code in src/auth and its test in tests/auth
    (in tests/ when ``auth_folder`` is false, and then tests/auth does not exist). billing's committed test fails
    when ``billing_fails``.
    """
    new_project(root, monkeypatch, capabilities=AUTH_AND_BILLING, commands=commands_block(log, scoped))
    write(root / "src/auth/login.py", "def login(): ...\n")
    write(root / "src/billing/pay.py", "def pay(): ...\n")
    write(root / "tests/billing/test_pay.py", "def test_pay():\n    assert " + ("False" if billing_fails else "True") + "\n")
    if auth_folder:
        write(root / "tests/auth/test_login.py", "def test_login():\n    assert True\n")
    on_a_branch(root, monkeypatch)
    run_json("new", REF, "--no-branch")
    change = root / ".specworks/changes/active" / REF
    write(change / "proposal.md", PROPOSAL)
    write(change / "specs/auth/spec.md", DELTA_AUTH)
    write(change / "tasks.md", TASKS)
    write(root / "src/auth/audit.py", tag("req", "REQ-AUTH-001") + "def audit(): ...\n")
    test_file = "tests/auth/test_audit.py" if auth_folder else "tests/test_audit.py"
    write(root / test_file, tag("ac", "AC-AUTH-001.1") + "def test_audit():\n    assert True\n")
    write_review(root, "None.\n")
    return root


def write_review(root, body):
    write(root / ".specworks/changes/active" / REF / "review.md", f"# Review: {REF}\n\n## Findings\n\n{body}\n")


def gate_review(*extra):
    return run_json("gate", "review", "--change", REF, "--base", "main", *extra)


def checks(data):
    return {c["name"].split(" (base")[0]: c for c in data["checks"]}


def mentions(check, text):
    return any(text in detail for detail in check["details"])


# --- the review gate's tests ------------------------------------------------------


# @ac AC-FLOW-017.1
def test_ac_flow_017_1_only_the_touched_capabilitys_tests(tmp_path, monkeypatch, log):
    make_project(tmp_path, monkeypatch, log)  # tests/billing holds a failing test
    code, data = gate_review()
    c = checks(data)
    assert code == 0 and data["passed"] is True, data
    assert runs(log, tmp_path) == [("scoped", ["tests/auth"], ".")]
    assert c[SCOPED]["ok"] and mentions(c[SCOPED], "tests/auth") and not mentions(c[SCOPED], "tests/billing"), c[SCOPED]
    assert TESTS not in c


# @ac AC-FLOW-017.2
@pytest.mark.parametrize("changed", ["src/billing/pay.py", "tests/billing/test_pay.py"], ids=["code-path", "test-folder"])
def test_ac_flow_017_2_a_changed_file_touches_its_capability(tmp_path, monkeypatch, log, changed):
    make_project(tmp_path, monkeypatch, log, billing_fails=False)
    write(tmp_path / changed, (tmp_path / changed).read_text(encoding="utf-8") + "# changed\n")
    write_review(tmp_path, f"None.\n\n## Changed files without tags\n\n- `{changed}`: a comment\n")
    code, data = gate_review()
    c = checks(data)
    assert code == 0 and data["passed"] is True, data
    assert runs(log, tmp_path) == [("scoped", ["tests/auth", "tests/billing"], ".")]
    assert mentions(c[SCOPED], "tests/auth") and mentions(c[SCOPED], "tests/billing"), c[SCOPED]


# @ac AC-FLOW-017.3
def test_ac_flow_017_3_no_scoped_test_command(tmp_path, monkeypatch, log):
    make_project(tmp_path, monkeypatch, log, scoped=False, auth_folder=False, billing_fails=False)  # tests/auth does not exist
    code, data = gate_review()
    c = checks(data)
    assert code == 0 and data["passed"] is True, data
    assert runs(log, tmp_path) == [("full", [], ".")]
    assert c[TESTS]["ok"] and SCOPED not in c
    assert not any(mentions(check, "tests/auth") for check in data["checks"]), data  # no warning about test folders


# @ac AC-FLOW-017.4
def test_ac_flow_017_4_a_touched_capability_without_a_test_folder(tmp_path, monkeypatch, log):
    make_project(tmp_path, monkeypatch, log, auth_folder=False, billing_fails=False)  # tests/auth does not exist
    write(tmp_path / "src/billing/pay.py", "def pay(): return 1\n")  # billing touched too
    write_review(tmp_path, "None.\n\n## Changed files without tags\n\n- `src/billing/pay.py`: a refactor\n")
    code, data = gate_review()
    c = checks(data)
    assert code == 0 and data["passed"] is True, data
    assert runs(log, tmp_path) == [("full", [], ".")]
    assert c[TESTS]["ok"] and SCOPED not in c
    warnings = [check for check in data["checks"] if not check["ok"] and not check["blocking"] and mentions(check, "tests/auth")]
    assert len(warnings) == 1 and not mentions(warnings[0], "tests/billing"), data


# @ac AC-FLOW-017.5
def test_ac_flow_017_5_no_capability_touched(tmp_path, monkeypatch, log):
    new_project(tmp_path, monkeypatch, capabilities=AUTH_AND_BILLING, commands=commands_block(log))
    write(tmp_path / "src/auth/login.py", "def login(): ...\n")
    write(tmp_path / "tests/auth/test_login.py", "def test_login():\n    assert True\n")
    on_a_branch(tmp_path, monkeypatch)
    run_json("new", REF, "--no-branch")
    write(tmp_path / "tests/test_integration.py", "def test_flow():\n    assert True\n")
    write(tmp_path / "README.md", "docs\n")
    write_review(tmp_path, "None.\n\n## Changed files without tags\n\n- `tests/test_integration.py`: an integration test\n")
    code, data = gate_review()
    c = checks(data)
    assert runs(log, tmp_path) == [("full", [], ".")], data
    assert TESTS in c and c[TESTS]["ok"] and SCOPED not in c, data


# @ac AC-FLOW-017.6
def test_ac_flow_017_6_failing_scoped_tests(tmp_path, monkeypatch, log):
    make_project(tmp_path, monkeypatch, log, billing_fails=False)
    write(tmp_path / "tests/auth/test_audit.py", tag("ac", "AC-AUTH-001.1") + "def test_audit():\n    assert False\n")
    code, data = gate_review()
    c = checks(data)
    assert code == 1 and not c[SCOPED]["ok"] and c[SCOPED]["blocking"] and mentions(c[SCOPED], "tests/auth"), data
    write_review(tmp_path, "- [ ] R1 **code-gap** the audit is not written\n  - **Decision**: back to code: write it\n")
    code, data = gate_review("--allow-open")
    c = checks(data)
    assert code == 0 and data["passed"] is True, data
    assert not c[SCOPED]["ok"] and not c[SCOPED]["blocking"], c[SCOPED]


# @ac AC-FLOW-017.7
def test_ac_flow_017_7_a_touched_capability_in_another_module(tmp_path, monkeypatch, log):
    new_project(tmp_path, monkeypatch, capabilities="  auth:\n    path: src/auth\n    prefix: AUTH\n", commands=commands_block(log))
    billing = add_billing_module(tmp_path, "tests_dir: spec\n")
    cfg = billing / ".specworks/config.yml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("commands:\n  test:\n  lint:\n", commands_block(log)), encoding="utf-8")
    write(tmp_path / "src/auth/login.py", "def login(): ...\n")
    on_a_branch(tmp_path, monkeypatch)
    run_json("new", REF, "--no-branch")
    change = tmp_path / ".specworks/changes/active" / REF
    write(change / "proposal.md", PROPOSAL)
    write(change / "specs/auth/spec.md", DELTA_AUTH)
    write(change / "specs/billing/invoices/spec.md", DELTA_INVOICES)
    write(change / "tasks.md", TASKS_INVOICES)
    write(tmp_path / "src/auth/audit.py", tag("req", "REQ-AUTH-001") + "def audit(): ...\n")
    write(tmp_path / "tests/auth/test_audit.py", tag("ac", "AC-AUTH-001.1") + "def test_audit():\n    assert True\n")
    write(billing / "src/invoices/send.py", tag("req", "REQ-BILLING-INVOICES-001") + "def send(): ...\n")
    write(billing / "spec/invoices/test_send.py", tag("ac", "AC-BILLING-INVOICES-001.1") + "def test_send():\n    assert True\n")
    write_review(tmp_path, "None.\n")
    code, data = gate_review()
    assert code == 0 and data["passed"] is True, data
    assert sorted(runs(log, tmp_path)) == [("scoped", ["spec/invoices"], "services/billing"), ("scoped", ["tests/auth"], ".")]
    write(billing / "spec/invoices/test_send.py", tag("ac", "AC-BILLING-INVOICES-001.1") + "def test_send():\n    assert False\n")
    code, data = gate_review()
    c = checks(data)
    assert code == 1 and not c[SCOPED]["ok"] and c[SCOPED]["blocking"], data


# @ac AC-FLOW-017.8
def test_ac_flow_017_8_validate_runs_everything(tmp_path, monkeypatch, log):
    make_project(tmp_path, monkeypatch, log)  # auth touched only; tests/billing holds a failing test
    run_json("phase", "review", "--change", REF)
    code, data = run_json("validate", "--change", REF, "--base", "main")
    c = checks(data)
    assert code == 1 and not c[TESTS]["ok"], data
    assert runs(log, tmp_path) == [("full", [], ".")]
