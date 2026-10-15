"""Design phase: the design gate (API recorded in design.md, stubs exist, build and tests still pass)."""

import json
import re
import sys

import pytest
from helpers import REF, run_json

from specworks.phases.gate import interface_files

PASS = f'"{sys.executable}" -c "print(\'all green\')"'
FAIL = f'"{sys.executable}" -c "import sys; print(\'ImportError: cannot import ResetService\'); sys.exit(1)"'
INTERFACES = (
    "# Design: add-password-reset\n\n## Decisions\n\nToken by email.\n\n## Interfaces\n\n{body}\n\n## Risks / Trade-offs\n\n- none\n"
)


def set_commands(root, **commands):
    cfg = root / "spec.yml"
    text = cfg.read_text()
    block = "".join(f"  {key}: {json.dumps(value)}\n" for key, value in commands.items())
    cfg.write_text(re.sub(r"(?m)^commands:\n(  .*\n)*", lambda _: "commands:\n" + block, text, count=1))


def write_design(root, body):
    (root / "spec/changes" / REF / "design.md").write_text(INTERFACES.format(body=body))


def gate(*extra):
    code, data = run_json("gate", "design", "--change", REF, *extra)
    return code, {c["name"]: c for c in data["checks"]}


SECTION = 'design.md has an Interfaces section (write "None" when the API does not change)'
FILES = "every file named under Interfaces exists"
TESTS = "the existing tests still pass with the stubs (commands.test)"


@pytest.fixture
def planned(project):
    set_commands(project, test=PASS)
    return project


def test_phase_order_has_interface_between_propose_and_test(planned):
    code, data = run_json("phase", REF, "design")
    assert code == 0 and data["phase"] == "design"
    code, data = run_json("status", "--change", REF)
    assert data["phase"] == "design" and data["phases"].index("specify") < data["phases"].index("design") < data["phases"].index("test")


def test_gate_needs_the_interfaces_section(planned):
    code, checks = gate()
    assert code == 1 and not checks[SECTION]["ok"]
    write_design(planned, "<!-- Public APIs ... -->")  # the template comment alone does not count
    code, checks = gate()
    assert code == 1 and not checks[SECTION]["ok"]


def test_gate_checks_the_named_files_exist(planned):
    write_design(
        planned,
        "- `src/auth/reset.py:ResetService`: `request_reset(email: str) -> None` (REQ-AUTH-003)\n"
        "- `src/auth/errors.py`: `ExpiredToken` (REQ-AUTH-003)",
    )
    code, checks = gate()
    assert code == 1 and checks[FILES]["details"] == ["src/auth/reset.py", "src/auth/errors.py"]
    (planned / "src/auth/reset.py").write_text("class ResetService:\n    def request_reset(self, email): raise NotImplementedError\n")
    (planned / "src/auth/errors.py").write_text("class ExpiredToken(Exception): ...\n")
    code, checks = gate()
    assert code == 0 and checks[FILES]["ok"] and checks[TESTS]["ok"]


def test_none_passes_without_files(planned):
    write_design(planned, "None. The change only fixes the lockout counter.")
    code, checks = gate()
    assert code == 0 and checks[SECTION]["ok"] and len([c for c in checks.values() if not c["ok"]]) == 0


def test_prose_without_paths_is_a_warning(planned):
    write_design(planned, "A ResetService with request_reset and confirm.")
    code, checks = gate()
    warning = checks["Interfaces names the file of each interface (`src/auth/reset.py`)"]
    assert code == 0 and not warning["ok"] and warning["blocking"] is False


def test_stubs_that_break_the_existing_tests_fail_the_gate(planned):
    write_design(planned, "None.")
    set_commands(planned, test=FAIL)
    code, checks = gate()
    assert code == 1 and "ImportError: cannot import ResetService" in checks[TESTS]["details"]
    code, checks = gate("--no-run")
    assert code == 0 and checks[TESTS]["blocking"] is False and "not run" in checks[TESTS]["details"][0]


def test_build_and_typecheck_run_when_configured(planned):
    write_design(planned, "None.")
    code, checks = gate()
    assert not any("commands.build" in name or "commands.typecheck" in name for name in checks)
    set_commands(planned, test=PASS, build=PASS, typecheck=FAIL)
    code, checks = gate()
    assert code == 1
    assert checks["the stubs build (commands.build)"]["ok"] and not checks["the stubs build (commands.typecheck)"]["ok"]


def test_invalid_specs_fail_the_gate(planned):
    write_design(planned, "None.")
    delta = planned / "spec/changes" / REF / "specs/user-auth/spec.md"
    delta.write_text(delta.read_text().replace("SHALL", "should"))
    code, checks = gate()
    assert code == 1 and not checks["specs and tasks are valid (specworks check)"]["ok"]


@pytest.mark.parametrize(
    "section, files",
    [
        ("`src/a.py`, `src/a.py:Thing`, `pkg/b.ts#run`, `lib/c.go(x)`", ["src/a.py", "pkg/b.ts", "lib/c.go"]),
        ("`ResetService`, `request_reset(email)`, `None`", []),
        ("`docs/` and `Makefile` and `a/b`", []),
    ],
)
def test_interface_files(section, files):
    assert interface_files(section) == files
