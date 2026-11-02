"""Code phase support: `specworks run` and the code gate."""

import json
import re
import sys

import pytest
from typer.testing import CliRunner

from helpers import REF, run_json, write_tests
from specworks.cli import app

runner = CliRunner()
PASS = f'"{sys.executable}" -c "print(\'all green\')"'
FAIL = f'"{sys.executable}" -c "import sys; print(\'2 failed\'); sys.exit(3)"'


def set_test_command(root, command):
    cfg = root / ".specworks/config.yml"
    text = cfg.read_text()
    cfg.write_text(re.sub(r"(?m)^  test:.*$", lambda _: f"  test: {json.dumps(command)}", text, count=1))


def set_command(key, command):
    code, data = run_json("config", "set", f"commands.{key}", command)
    assert code == 0, data


def implement_everything(root):
    """Tests for every AC, @req tags for every requirement, every task ticked."""
    write_tests(root, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    (root / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\ndef reset(): ...\n")  # specworks: ignore-tags
    (root / "src/auth/lockout.py").write_text("# @req REQ-AUTH-002\nLIMIT = 3\n")  # specworks: ignore-tags
    run_json("task", "done", "1.1", "1.2", "--change", REF)


def implement_code_only(root):
    """@req tags for every requirement and every task ticked, but no @ac test of the change."""
    (root / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\ndef reset(): ...\n")  # specworks: ignore-tags
    (root / "src/auth/lockout.py").write_text("# @req REQ-AUTH-002\nLIMIT = 3\n")  # specworks: ignore-tags
    run_json("task", "done", "1.1", "1.2", "--change", REF)


def checks(data):
    return {c["name"]: c for c in data["checks"]}


def task_checks(data):
    """The gate's checks on open tasks (not `specworks check`)."""
    return [c for c in data["checks"] if "task" in c["name"] and "done" in c["name"]]


BUILD = "the code builds (commands.build)"
TYPECHECK = "typecheck passes (commands.typecheck)"
LINT = "lint passes (commands.lint)"
COMMAND_CHECKS = {"build": BUILD, "typecheck": TYPECHECK, "lint": LINT}
NO_COMMANDS = "build, typecheck and lint"
NO_COMMANDS_WARNING = "no build, typecheck or lint command configured: the tests run in review"


# --- specworks run ----------------------------------------------------------


# @ac AC-PROJ-013.1
def test_run_passes_the_exit_code_through(project):
    set_test_command(project, FAIL)
    code, data = run_json("run", "test")
    assert code == 3 and data["ok"] is False and data["tail"] == ["2 failed"]
    set_test_command(project, PASS)
    code, data = run_json("run", "test", "--change", REF)
    assert code == 0 and data["ok"] is True and data["cwd"] == "."


# @ac AC-PROJ-013.2
def test_run_in_the_module_of_the_change(project):
    runner.invoke(app, ["module", "add", "web"])
    web_cfg = project / "web/.specworks/config.yml"
    pwd = f'"{sys.executable}" -c "import os; print(os.path.basename(os.getcwd()))"'
    web_cfg.write_text(web_cfg.read_text().replace("commands:\n  test:\n", f"commands:\n  test: {json.dumps(pwd)}\n"))
    run_json("new", "web-change", "--module", "web", "--no-branch")
    code, data = run_json("run", "test", "--change", "web:web-change")
    assert code == 0 and data["cwd"] == "web" and data["tail"] == ["web"]


# @ac AC-PROJ-013.3
def test_run_unconfigured_command(project):
    code, data = run_json("run", "lint")
    assert code == 1 and "no 'lint' command configured" in data["error"]
    assert "(e.g. lint: <command>)" in data["error"]


# @ac AC-PROJ-013.4
def test_run_unknown_command_key(project):
    code, data = run_json("run", "frobnicate")
    assert code == 1 and "unknown command 'frobnicate'" in data["error"]
    assert "test, lint, typecheck, build, format" in data["error"] and "commands:" not in data["error"]


# --- gate code ---------------------------------------------------------


# @ac AC-FLOW-008.1
def test_ac_flow_008_1_code_gate_passes_and_shows_each_command_it_ran(project):
    for key in COMMAND_CHECKS:
        set_command(key, PASS)
    implement_everything(project)
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 0 and data["passed"] is True, data
    c = checks(data)
    for name in COMMAND_CHECKS.values():
        assert c[name]["ok"] is True and c[name]["details"][0].startswith("$ ") and "all green" in c[name]["details"][0], c[name]
    assert NO_COMMANDS not in c


# @ac AC-FLOW-008.2
def test_implement_gate_lists_what_is_missing(project):
    set_command("build", PASS)
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    (project / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\n")  # specworks: ignore-tags
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1
    c = checks(data)
    assert c["every requirement has code (@req tag)"]["details"] == ["REQ-AUTH-002"]
    tasks = task_checks(data)  # 1.1 [test] and 1.2 [code] are open: only the [code] one is listed
    assert len(tasks) == 1 and tasks[0]["blocking"] and [d.split()[0] for d in tasks[0]["details"]] == ["1.2"], tasks


# @ac AC-FLOW-008.3
@pytest.mark.parametrize("failing", ["build", "typecheck", "lint"])
def test_ac_flow_008_3_a_failing_command_fails_the_gate_with_its_output(project, failing):
    for key in COMMAND_CHECKS:
        set_command(key, FAIL if key == failing else PASS)
    implement_everything(project)  # the change's own @ac tests do not soften a failing command
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1 and data["passed"] is False
    c = checks(data)
    failed = c[COMMAND_CHECKS[failing]]
    assert failed["ok"] is False and failed["blocking"] is True and "2 failed" in failed["details"], failed
    assert all(c[COMMAND_CHECKS[key]]["ok"] for key in COMMAND_CHECKS if key != failing)


# @ac AC-FLOW-008.6
def test_code_gate_does_not_need_a_test_for_every_criterion(project):
    set_command("build", PASS)
    implement_code_only(project)
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 0 and data["passed"] is True, data
    assert not any("acceptance criterion has a test" in c["name"] for c in data["checks"])


# @ac AC-FLOW-008.4
def test_ac_flow_008_4_no_build_typecheck_or_lint_command_passes_with_a_warning(project):
    implement_everything(project)
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 0 and data["passed"] is True, data
    c = checks(data)
    assert c[NO_COMMANDS]["ok"] is True and c[NO_COMMANDS]["blocking"] is False and c[NO_COMMANDS]["details"] == [NO_COMMANDS_WARNING]
    assert not set(COMMAND_CHECKS.values()) & set(c)


# @ac AC-FLOW-008.9
@pytest.mark.parametrize("test_command", [FAIL, None])
def test_ac_flow_008_9_the_code_gate_does_not_run_the_test_command(project, test_command):
    if test_command:
        set_test_command(project, test_command)
    set_command("build", PASS)
    implement_code_only(project)  # no @ac test of the change: a red suite would have blocked before
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 0 and data["passed"] is True, data
    assert not any("commands.test" in c["name"] or "test suite" in c["name"] for c in data["checks"])
    assert not any("2 failed" in d or "'test' command" in d for c in data["checks"] for d in c["details"])


# @ac AC-FLOW-008.10
def test_ac_flow_008_10_only_the_configured_typecheck_runs(project):
    set_test_command(project, FAIL)
    set_command("typecheck", PASS)
    implement_everything(project)
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 0 and data["passed"] is True, data
    names = [c["name"] for c in data["checks"]]
    assert TYPECHECK in names and checks(data)[TYPECHECK]["details"][0].startswith("$ ")
    assert BUILD not in names and LINT not in names and NO_COMMANDS not in names


# @ac AC-FLOW-003.2
def test_no_run_turns_the_command_checks_into_warnings(project):
    set_command("build", PASS)
    implement_everything(project)
    code, data = run_json("gate", "code", "--change", REF, "--no-run")
    assert code == 0
    build = checks(data)[BUILD]
    assert build["blocking"] is False and "not run" in build["details"][0]


# @ac AC-FLOW-008.5
def test_removed_requirement_still_tagged_blocks_implement(project):
    set_command("build", PASS)
    implement_everything(project)
    delta = project / ".specworks/changes/active" / REF / "specs/user-auth/spec.md"
    delta.write_text(
        delta.read_text()
        + "\n## REMOVED Requirements\n\n### Requirement: REQ-AUTH-001 Password login\n**Reason**: SSO only\n**Migration**: use SSO\n"
    )
    tasks = project / ".specworks/changes/active" / REF / "tasks.md"
    tasks.write_text(tasks.read_text() + "- [x] 2.2 Remove password login (REQ-AUTH-001)\n")
    (project / "src/auth/login.py").write_text("# @req REQ-AUTH-001\n")  # specworks: ignore-tags
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1 and checks(data)["removed requirements and criteria are gone from tests and code"]["details"] == ["REQ-AUTH-001"]


# @ac AC-FLOW-008.5
def test_criteria_of_a_removed_requirement_still_tested_block_implement(project):
    # Its code is gone, but a test of its criterion would point to an unknown ID after close.
    set_command("build", PASS)
    implement_everything(project)
    delta = project / ".specworks/changes/active" / REF / "specs/user-auth/spec.md"
    delta.write_text(
        delta.read_text()
        + "\n## REMOVED Requirements\n\n### Requirement: REQ-AUTH-001 Password login\n**Reason**: SSO only\n**Migration**: use SSO\n"
    )
    tasks = project / ".specworks/changes/active" / REF / "tasks.md"
    tasks.write_text(tasks.read_text() + "- [x] 2.2 Remove password login (REQ-AUTH-001)\n")
    (project / "tests/test_login.py").write_text("# @ac AC-AUTH-001.1\ndef test_login(): ...\n")  # specworks: ignore-tags
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1 and checks(data)["removed requirements and criteria are gone from tests and code"]["details"] == ["AC-AUTH-001.1"]
    (project / "tests/test_login.py").unlink()
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 0, data



# @ac AC-FLOW-008.5
def test_criterion_a_modified_requirement_drops_must_lose_its_tests(project):
    # The living REQ-AUTH-002 has AC-AUTH-002.2; the change's MODIFIED block keeps only .1.
    living = project / "src/auth/docs/spec.md"
    living.write_text(living.read_text() + "\n#### Scenario: AC-AUTH-002.2 Unlock by email\n- **WHEN** the user follows the email link\n- **THEN** the account is unlocked\n")
    set_command("build", PASS)
    implement_everything(project)
    (project / "tests/test_unlock.py").write_text("# @ac AC-AUTH-002.2\ndef test_unlock(): ...\n")  # specworks: ignore-tags
    code, data = run_json("gate", "test", "--change", REF)
    assert code == 0 and checks(data)["removed requirements and criteria are gone from tests and code"]["details"] == ["AC-AUTH-002.2"]
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1 and checks(data)["removed requirements and criteria are gone from tests and code"]["details"] == ["AC-AUTH-002.2"]
    code, data = run_json("trace", "--change", REF)
    assert data["gaps"]["acWithoutTests"] == []  # a dropped criterion needs no test
    (project / "tests/test_unlock.py").unlink()
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 0, data

def test_tag_scan_skips_files_too_large_or_not_text(project):
    (project / "src/auth/lockout.py").write_text("# @req REQ-AUTH-002\nLIMIT = 3\n")  # specworks: ignore-tags
    (project / "src/auth/big.py").write_text("# @req REQ-AUTH-003\n" + "x = 1\n" * 200_000)  # over 1 MB: not read  # specworks: ignore-tags
    (project / "src/auth/legacy.py").write_bytes("# @req REQ-AUTH-003 café\n".encode("latin-1"))  # not UTF-8: not read  # specworks: ignore-tags
    code, data = run_json("trace", "--change", REF)
    assert data["gaps"]["reqWithoutCode"] == ["REQ-AUTH-003"]


def test_tag_scan_follows_a_symlink_to_a_file_outside_the_workspace(project, tmp_path_factory):
    shared = tmp_path_factory.mktemp("shared") / "reset.py"
    shared.write_text("# @req REQ-AUTH-003\n")  # specworks: ignore-tags
    try:
        (project / "src/auth/reset.py").symlink_to(shared)
    except OSError:  # Windows without the symlink privilege
        pytest.skip("cannot create symlinks here")
    code, data = run_json("trace", "--change", REF)
    assert "REQ-AUTH-003" not in data["gaps"]["reqWithoutCode"]
    assert any("src/auth/reset.py:1" in code_at for row in data["rows"] for code_at in row["code"])


# @ac AC-FLOW-008.3
def test_a_command_writing_bytes_that_are_not_text_does_not_crash_the_gate(project):
    set_command("build", f'"{sys.executable}" -c "import sys; sys.stdout.buffer.write(bytes([0xff, 0xfe, 10])); sys.exit(1)"')
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1 and not checks(data)[BUILD]["ok"]
