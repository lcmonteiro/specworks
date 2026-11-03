"""A capability's test folder, the scoped test command, and the review gate running only the touched capabilities' tests."""

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from helpers import init_repo, on_a_branch, run_json, runner
from specworks.cli import app
from specworks.core.runner import run_scoped, scoped_command
from specworks.core.workspace import load_workspace

REF = "add-login-audit"
TESTS = "the test suite passes (commands.test)"
SCOPED = "the touched capabilities' tests pass (commands.test_scoped)"

# A test command that records each run (its mode, its arguments and its folder) in a log outside the repo, and fails
# when a Python file under the folders it is given (the current folder for the full suite) holds `assert False`.
RECORDER = """\
import json, os, sys
log, mode, *paths = sys.argv[1:]
with open(log, "a", encoding="utf-8") as f:
    f.write(json.dumps({"mode": mode, "paths": paths, "cwd": os.getcwd()}) + "\\n")
failing = []
for top in paths or ["."]:
    for folder, _, names in os.walk(top):
        for name in names:
            if name.endswith(".py"):
                with open(os.path.join(folder, name), encoding="utf-8") as source:
                    if "assert False" in source.read():
                        failing.append(os.path.join(folder, name))
print(mode, len(paths), "failed" if failing else "passed")
sys.exit(1 if failing else 0)
"""

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
    """A tag line for a sample project's file, built here so this repo's own trace does not read it."""
    return f"# @{kind} {ids}\n"


def quoted(path):
    """A folder quoted for the platform's shell, as the scoped command fills it in."""
    return subprocess.list2cmdline([path]) if os.name == "nt" else shlex.quote(path)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def recorder_command(recorder, log, mode, placeholder=""):
    return json.dumps(f'"{sys.executable}" "{recorder}" "{log}" {mode}{placeholder}')


@pytest.fixture
def log(tmp_path_factory):
    """The run log of the recorder test commands, outside every sample project, and the recorder itself."""
    folder = tmp_path_factory.mktemp("runs")
    recorder = folder / "recorder.py"
    recorder.write_text(RECORDER, encoding="utf-8")
    run_log = folder / "runs.jsonl"
    run_log.write_text("", encoding="utf-8")
    return recorder, run_log


def commands_block(log, scoped=True):
    recorder, run_log = log
    lines = f"commands:\n  test: {recorder_command(recorder, run_log, 'full')}\n"
    if scoped:
        lines += f"  test_scoped: {recorder_command(recorder, run_log, 'scoped', ' {paths}')}\n"
    return lines


def runs(log, root):
    """Each recorded run as (mode, folders, folder it ran in relative to ``root``)."""
    _, run_log = log
    entries = [json.loads(line) for line in run_log.read_text(encoding="utf-8").splitlines() if line]
    return [(e["mode"], e["paths"], Path(e["cwd"]).resolve().relative_to(root.resolve()).as_posix()) for e in entries]


def new_project(root, monkeypatch, config_tail="", capabilities="", commands="commands:\n  test:\n  lint:\n"):
    monkeypatch.chdir(root)
    init_repo(root)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    cfg = root / ".specworks/config.yml"
    text = cfg.read_text(encoding="utf-8")
    text = text.replace("capabilities: {}", f"capabilities:\n{capabilities}" if capabilities else "capabilities: {}")
    text = text.replace("commands:\n  test:\n  lint:\n", commands)
    cfg.write_text(text + config_tail, encoding="utf-8")
    return root


AUTH_AND_BILLING = "  auth:\n    path: src/auth\n    prefix: AUTH\n  billing:\n    path: src/billing\n    prefix: BILL\n"


def make_project(root, monkeypatch, log, *, scoped=True, auth_folder=True, billing_fails=True):
    """Capabilities auth (src/auth) and billing (src/billing), each with a test folder under tests/, committed on main;
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


# --- a capability's test folder -------------------------------------------------


def folder_of(root, name):
    ws = load_workspace(root)
    (mod, cap), *_ = [(m, c) for m, c in ws.capabilities() if m.qualify(c.name) == name]
    return cap.tests_path(mod.root, mod.config.tests_dir)


# @ac AC-PROJ-027.1
def test_ac_proj_027_1_the_default_test_folder(tmp_path, monkeypatch):
    new_project(tmp_path, monkeypatch, capabilities="  auth:\n    path: src/auth\n")
    assert folder_of(tmp_path, "auth") == tmp_path / "tests/auth"
    assert not (tmp_path / "tests/auth").exists()  # known whether or not it exists


# @ac AC-PROJ-027.2
def test_ac_proj_027_2_the_modules_tests_dir(tmp_path, monkeypatch):
    new_project(tmp_path, monkeypatch, capabilities="  auth:\n    path: src/auth\n", config_tail="tests_dir: test\n")
    assert folder_of(tmp_path, "auth") == tmp_path / "test/auth"


# @ac AC-PROJ-027.3
@pytest.mark.parametrize("tests_dir", ["", "tests_dir: spec\n"], ids=["default", "spec"])
def test_ac_proj_027_3_a_capabilitys_own_tests_folder(tmp_path, monkeypatch, tests_dir):
    new_project(tmp_path, monkeypatch, capabilities="  auth:\n    path: src/auth\n    tests: src/auth\n", config_tail=tests_dir)
    assert folder_of(tmp_path, "auth") == tmp_path / "src/auth"


def add_billing_module(root, billing_config=""):
    """Module billing at services/billing with capability invoices (src/invoices) and ``billing_config`` appended."""
    assert runner.invoke(app, ["module", "add", "services/billing"]).exit_code == 0
    cfg = root / "services/billing/.specworks/config.yml"
    text = cfg.read_text(encoding="utf-8").replace("capabilities: {}", "capabilities:\n  invoices:\n    path: src/invoices")
    cfg.write_text(text + billing_config, encoding="utf-8")
    return root / "services/billing"


# @ac AC-PROJ-027.4
def test_ac_proj_027_4_inside_a_module(tmp_path, monkeypatch):
    new_project(tmp_path, monkeypatch, capabilities="  auth:\n    path: src/auth\n", config_tail="tests_dir: tests\n")
    add_billing_module(tmp_path, "tests_dir: spec\n")
    assert folder_of(tmp_path, "billing:invoices") == tmp_path / "services/billing/spec/invoices"
    assert folder_of(tmp_path, "auth") == tmp_path / "tests/auth"


# --- config checks ----------------------------------------------------------------


# @ac AC-PROJ-003.1
@pytest.mark.parametrize(
    "tests", ["../outside", "/etc", "src/../../outside"], ids=["up", "absolute", "inner-up"],
)
def test_ac_proj_003_1_a_capabilitys_tests_stays_inside_the_project(tmp_path, monkeypatch, tests):
    new_project(tmp_path, monkeypatch, capabilities=f"  auth:\n    path: src/auth\n    tests: {tests}\n")
    code, data = run_json("context")
    assert code == 1 and "must be a relative folder inside the project" in data["error"], data
    assert "auth" in data["error"] and "tests" in data["error"], data  # names the setting


# @ac AC-PROJ-003.1
@pytest.mark.parametrize("capabilities, tail", [("", "tests_dir: 3\n"), ("  auth:\n    path: src/auth\n    tests: ''\n", "")], ids=["tests_dir", "tests"])
def test_ac_proj_003_1_a_test_folder_must_be_a_non_empty_string(tmp_path, monkeypatch, capabilities, tail):
    new_project(tmp_path, monkeypatch, capabilities=capabilities, config_tail=tail)
    code, data = run_json("context")
    assert code == 1 and "tests" in data["error"], data


# @ac AC-PROJ-003.8
def test_ac_proj_003_8_a_scoped_test_command_without_its_placeholder(tmp_path, monkeypatch):
    new_project(tmp_path, monkeypatch, commands="commands:\n  test: uv run pytest\n  test_scoped: uv run pytest\n")
    code, data = run_json("context")
    assert code == 1 and "commands.test_scoped" in data["error"] and "{paths}" in data["error"], data
    cfg = tmp_path / ".specworks/config.yml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("  test_scoped: uv run pytest\n", "  test_scoped: uv run pytest {paths}\n"), encoding="utf-8")
    code, data = run_json("context")
    assert code == 0 and data["commands"]["test_scoped"] == "uv run pytest {paths}", data


# --- running the scoped tests -----------------------------------------------------


# @ac AC-PROJ-028.1
def test_ac_proj_028_1_the_folders_filled_in(tmp_path, monkeypatch):
    new_project(tmp_path, monkeypatch, commands="commands:\n  test: uv run pytest\n  test_scoped: uv run pytest {paths}\n")
    ws = load_workspace(tmp_path)
    command = scoped_command(ws, ws.top, [tmp_path / "tests/auth", tmp_path / "tests/my tests"])
    assert command == f"uv run pytest tests/auth {quoted('tests/my tests')}"


# @ac AC-PROJ-028.1
def test_ac_proj_028_1_a_test_folder_that_links_outside_the_module_keeps_its_own_path(tmp_path, monkeypatch, tmp_path_factory):
    new_project(tmp_path, monkeypatch, commands="commands:\n  test: uv run pytest\n  test_scoped: uv run pytest {paths}\n")
    shared = tmp_path_factory.mktemp("shared") / "auth"
    shared.mkdir()
    (tmp_path / "tests").mkdir(exist_ok=True)
    try:
        (tmp_path / "tests/auth").symlink_to(shared, target_is_directory=True)
    except OSError:  # Windows without the symlink privilege
        pytest.skip("cannot create symlinks here")
    ws = load_workspace(tmp_path)
    assert scoped_command(ws, ws.top, [tmp_path / "tests/auth"]) == "uv run pytest tests/auth"


# @ac AC-PROJ-028.1
def test_ac_proj_028_1_the_scoped_run_reports_its_exit_code_and_output(tmp_path, monkeypatch, log):
    new_project(tmp_path, monkeypatch, commands=commands_block(log))
    write(tmp_path / "tests/my tests/test_x.py", "def test_x():\n    assert False\n")
    ws = load_workspace(tmp_path)
    result = run_scoped(ws, ws.top, [tmp_path / "tests/auth", tmp_path / "tests/my tests"], reuse=False)
    assert runs(log, tmp_path) == [("scoped", ["tests/auth", "tests/my tests"], ".")]
    assert result.exit_code == 1 and not result.ok and result.cwd == "." and "scoped 2 failed" in result.output


# @ac AC-PROJ-028.2
def test_ac_proj_028_2_in_a_module(tmp_path, monkeypatch, log):
    new_project(tmp_path, monkeypatch, commands="commands:\n  test: uv run pytest\n")
    billing = add_billing_module(tmp_path, "tests_dir: spec\n")
    cfg = billing / ".specworks/config.yml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("commands:\n  test:\n  lint:\n", commands_block(log)), encoding="utf-8")
    ws = load_workspace(tmp_path)
    module = ws.module("billing")
    result = run_scoped(ws, module, [billing / "spec/invoices"], reuse=False)
    assert runs(log, tmp_path) == [("scoped", ["spec/invoices"], "services/billing")]
    assert result.ok and result.cwd == "services/billing", result


# @ac AC-PROJ-028.3
def test_ac_proj_028_3_reused_only_for_the_same_folders(tmp_path, monkeypatch, log):
    new_project(tmp_path, monkeypatch, commands=commands_block(log))
    on_a_branch(tmp_path, monkeypatch)
    ws = load_workspace(tmp_path)
    auth, billing = tmp_path / "tests/auth", tmp_path / "tests/billing"
    run_scoped(ws, ws.top, [auth])
    second = run_scoped(ws, ws.top, [auth, billing])
    assert len(runs(log, tmp_path)) == 2 and second.cached_at == ""  # other folders: a real run
    third = run_scoped(ws, ws.top, [auth, billing])
    assert len(runs(log, tmp_path)) == 2 and third.cached_at != "" and third.ok  # the same folders: reused


# --- specworks run test_scoped ----------------------------------------------------


# @ac AC-PROJ-013.5
def test_ac_proj_013_5_the_scoped_test_command_run_directly_is_refused(tmp_path, monkeypatch, log):
    new_project(tmp_path, monkeypatch, commands=commands_block(log))
    code, data = run_json("run", "test_scoped")
    assert code == 1 and "{paths}" in data["error"] and "review gate" in data["error"], data
    assert re.search(r"\btest\b", data["error"]), data  # points to `test` for the whole suite
    assert runs(log, tmp_path) == []  # nothing ran


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
