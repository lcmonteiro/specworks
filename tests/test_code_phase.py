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
    cfg = root / "spec.yml"
    text = cfg.read_text()
    cfg.write_text(re.sub(r"(?m)^  test:.*$", lambda _: f"  test: {json.dumps(command)}", text, count=1))


def implement_everything(root):
    """Tests for every AC, @req tags for every requirement, every task ticked."""
    write_tests(root, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    (root / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\ndef reset(): ...\n")  # specworks: ignore-tags
    (root / "src/auth/lockout.py").write_text("# @req REQ-AUTH-002\nLIMIT = 3\n")  # specworks: ignore-tags
    run_json("task", "done", "1.1", "1.2", "--change", REF)


def checks(data):
    return {c["name"]: c for c in data["checks"]}


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
    web_cfg = project / "web/spec.yml"
    pwd = f'"{sys.executable}" -c "import os; print(os.path.basename(os.getcwd()))"'
    web_cfg.write_text(web_cfg.read_text().replace("commands:\n  test:\n", f"commands:\n  test: {json.dumps(pwd)}\n"))
    run_json("new", "web-change", "--module", "web")
    code, data = run_json("run", "test", "--change", "web:web-change")
    assert code == 0 and data["cwd"] == "web" and data["tail"] == ["web"]


# @ac AC-PROJ-013.3
def test_run_unconfigured_command(project):
    code, data = run_json("run", "lint")
    assert code == 1 and "no 'lint' command configured" in data["error"]


# --- gate code ---------------------------------------------------------


def test_implement_gate_passes_when_everything_is_done(project):
    set_test_command(project, PASS)
    implement_everything(project)
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 0 and data["passed"] is True, data
    assert checks(data)["the test suite passes (commands.test)"]["details"][0].startswith("$ ")


def test_implement_gate_lists_what_is_missing(project):
    set_test_command(project, PASS)
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    (project / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\n")  # specworks: ignore-tags
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1
    c = checks(data)
    assert c["every requirement has code (@req tag)"]["details"] == ["REQ-AUTH-002"]
    assert [d.split()[0] for d in c["every task is done (specworks task list --pending)"]["details"]] == ["1.1", "1.2"]


def test_implement_gate_fails_when_tests_fail(project):
    set_test_command(project, FAIL)
    implement_everything(project)
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1
    tests = checks(data)["the test suite passes (commands.test)"]
    assert tests["ok"] is False and "2 failed" in tests["details"]


def test_implement_gate_needs_a_test_command(project):
    implement_everything(project)
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1 and "no 'test' command configured" in checks(data)["the test suite passes (commands.test)"]["details"][0]


def test_no_run_turns_the_test_check_into_a_warning(project):
    implement_everything(project)
    code, data = run_json("gate", "code", "--change", REF, "--no-run")
    assert code == 0
    tests = checks(data)["the test suite passes (commands.test)"]
    assert tests["blocking"] is False and "not run" in tests["details"][0]


def test_removed_requirement_still_tagged_blocks_implement(project):
    set_test_command(project, PASS)
    implement_everything(project)
    delta = project / "spec/changes" / REF / "specs/user-auth/spec.md"
    delta.write_text(
        delta.read_text()
        + "\n## REMOVED Requirements\n\n### Requirement: REQ-AUTH-001 Password login\n**Reason**: SSO only\n**Migration**: use SSO\n"
    )
    tasks = project / "spec/changes" / REF / "tasks.md"
    tasks.write_text(tasks.read_text() + "- [x] 2.2 Remove password login (REQ-AUTH-001)\n")
    (project / "src/auth/login.py").write_text("# @req REQ-AUTH-001\n")  # specworks: ignore-tags
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1 and checks(data)["removed requirements and criteria are gone from tests and code"]["details"] == ["REQ-AUTH-001"]


def test_criteria_of_a_removed_requirement_still_tested_block_implement(project):
    # Its code is gone, but a test of its criterion would point to an unknown ID after close.
    set_test_command(project, PASS)
    implement_everything(project)
    delta = project / "spec/changes" / REF / "specs/user-auth/spec.md"
    delta.write_text(
        delta.read_text()
        + "\n## REMOVED Requirements\n\n### Requirement: REQ-AUTH-001 Password login\n**Reason**: SSO only\n**Migration**: use SSO\n"
    )
    tasks = project / "spec/changes" / REF / "tasks.md"
    tasks.write_text(tasks.read_text() + "- [x] 2.2 Remove password login (REQ-AUTH-001)\n")
    (project / "tests/test_login.py").write_text("# @ac AC-AUTH-001.1\ndef test_login(): ...\n")  # specworks: ignore-tags
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1 and checks(data)["removed requirements and criteria are gone from tests and code"]["details"] == ["AC-AUTH-001.1"]
    (project / "tests/test_login.py").unlink()
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 0, data



def test_criterion_a_modified_requirement_drops_must_lose_its_tests(project):
    # The living REQ-AUTH-002 has AC-AUTH-002.2; the change's MODIFIED block keeps only .1.
    living = project / "src/auth/docs/spec.md"
    living.write_text(living.read_text() + "\n#### Scenario: AC-AUTH-002.2 Unlock by email\n- **WHEN** the user follows the email link\n- **THEN** the account is unlocked\n")
    set_test_command(project, PASS)
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


def test_a_command_writing_bytes_that_are_not_text_does_not_crash_the_gate(project):
    set_test_command(project, f'"{sys.executable}" -c "import sys; sys.stdout.buffer.write(bytes([0xff, 0xfe, 10])); sys.exit(1)"')
    code, data = run_json("gate", "code", "--change", REF)
    assert code == 1 and not checks(data)["the test suite passes (commands.test)"]["ok"]
