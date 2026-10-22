"""Design phase: the design gate (API recorded in design.md, stubs exist, build and tests still pass)."""

import json
import re
import sys

import pytest

from helpers import REF, run_json
from specworks.core.changes import load_change
from specworks.core.config import load_config
from specworks.workflow.gate import interface_files, interfaces_section

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


def change(root):
    return load_change(load_config(root), REF)


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


def test_phase_order_has_interface_between_propose_and_implement(planned):
    code, data = run_json("phase", "design", "--change", REF)
    assert code == 0 and data["phase"] == "design"
    code, data = run_json("status", "--change", REF)
    assert data["phase"] == "design" and data["phases"].index("specify") < data["phases"].index("design") < data["phases"].index("implement")


# @ac AC-FLOW-006.1
def test_gate_needs_the_interfaces_section(planned):
    code, checks = gate()
    assert code == 1 and not checks[SECTION]["ok"]
    write_design(planned, "<!-- Public APIs ... -->")  # the template comment alone does not count
    code, checks = gate()
    assert code == 1 and not checks[SECTION]["ok"]


# @ac AC-FLOW-006.2
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


# @ac AC-FLOW-006.3
def test_none_passes_without_files(planned):
    write_design(planned, "None. The change only fixes the lockout counter.")
    code, checks = gate()
    assert code == 0 and checks[SECTION]["ok"] and len([c for c in checks.values() if not c["ok"]]) == 0


# @ac AC-FLOW-006.3
def test_prose_without_paths_is_a_warning(planned):
    write_design(planned, "A ResetService with request_reset and confirm.")
    code, checks = gate()
    warning = checks["Interfaces names the file of each interface (`src/auth/reset.py`)"]
    assert code == 0 and not warning["ok"] and warning["blocking"] is False


# @ac AC-FLOW-003.2, AC-FLOW-006.4
def test_stubs_that_break_the_existing_tests_fail_the_gate(planned):
    write_design(planned, "None.")
    set_commands(planned, test=FAIL)
    code, checks = gate()
    assert code == 1 and "ImportError: cannot import ResetService" in checks[TESTS]["details"]
    code, checks = gate("--no-run")
    assert code == 0 and checks[TESTS]["blocking"] is False and "not run" in checks[TESTS]["details"][0]


# @ac AC-FLOW-006.5
def test_build_and_typecheck_run_when_configured(planned):
    write_design(planned, "None.")
    code, checks = gate()
    assert not any("commands.build" in name or "commands.typecheck" in name for name in checks)
    set_commands(planned, test=PASS, build=PASS, typecheck=FAIL)
    code, checks = gate()
    assert code == 1
    assert checks["the stubs build (commands.build)"]["ok"] and not checks["the stubs build (commands.typecheck)"]["ok"]


# @ac AC-FLOW-003.1
def test_invalid_specs_fail_the_gate(planned):
    write_design(planned, "None.")
    delta = planned / "spec/changes" / REF / "specs/user-auth/spec.md"
    delta.write_text(delta.read_text().replace("SHALL", "should"))
    code, checks = gate()
    assert code == 1 and not checks["specs and tasks are valid (specworks check)"]["ok"]


# @ac AC-FLOW-006.2
@pytest.mark.parametrize(
    "section, files",
    [
        ("`src/a.py`, `src/a.py:Thing`, `pkg/b.ts#run`, `lib/c.go(x)`", ["src/a.py", "pkg/b.ts", "lib/c.go"]),
        ("`ResetService`, `request_reset(email)`, `None`", []),
        ("`docs/` and `Makefile` and `a/b`", []),
        ("`main.py`, `cli.ts:run`, `ResetService.request_reset`, `obj.method()`, `v1.2`", ["main.py", "cli.ts"]),
    ],
)
def test_interface_files(section, files):
    assert interface_files(section) == files


# @ac AC-FLOW-006.4
def test_red_suite_is_only_a_warning_once_the_change_has_tests(planned):
    # `/specworks-test` re-checks `gate design`, and a later build cycle reopens the API:
    # by then this change's own @ac tests are red on purpose.
    write_design(planned, "None.")
    set_commands(planned, test=FAIL)
    (planned / "tests").mkdir()
    (planned / "tests/test_other.py").write_text("# @ac AC-OTHER-001.1\ndef test_other(): ...\n")  # not this change  # specworks: ignore-tags
    code, checks = gate()
    assert code == 1 and checks[TESTS]["blocking"] is True
    (planned / "tests/test_reset.py").write_text("# @ac AC-AUTH-003.1\ndef test_request(): assert False\n")  # specworks: ignore-tags
    code, checks = gate()
    assert code == 0 and checks[TESTS]["ok"] is False and checks[TESTS]["blocking"] is False
    assert "already has @ac tests" in checks[TESTS]["details"][0]


# @ac AC-FLOW-006.1
@pytest.mark.parametrize(
    "design, files",
    [
        # Any case and any qualifier after "Interfaces".
        ("## Decisions\n\nx\n\n## Interfaces (API)\n\n- `src/auth/reset.py`: `reset()`\n\n## Risks\n\n- `src/other/x.py`\n", ["src/auth/reset.py"]),
        ("## interfaces\n\n- `src/auth/reset.py`: `reset()`\n", ["src/auth/reset.py"]),
        # A "## " line inside a code fence does not end the section.
        ("## Interfaces\n\n```md\n## Example\n```\n\n- `src/auth/reset.py`: `reset()`\n\n## Risks\n", ["src/auth/reset.py"]),
    ],
)
def test_interfaces_section_is_found_by_its_heading(planned, design, files):
    (planned / "spec/changes" / REF / "design.md").write_text(f"# Design\n\n{design}")
    (planned / "src/auth/reset.py").write_text("def reset(): raise NotImplementedError\n")
    code, checks = gate()
    assert checks[SECTION]["ok"] is True
    assert interface_files(interfaces_section(change(planned))) == files


# @ac AC-FLOW-006.1
def test_no_interfaces_heading_means_no_section(planned):
    (planned / "spec/changes" / REF / "design.md").write_text("# Design\n\n## Interfaced systems\n\n- `src/auth/reset.py`\n")
    code, checks = gate()
    assert checks[SECTION]["ok"] is False


# @ac AC-FLOW-006.6
def test_a_module_change_needs_its_interface_files_in_the_module(planned):
    assert run_json("module", "add", "services/billing")[0] == 0
    run_json("new", "add-invoices", "--module", "billing", "--no-branch")
    design = planned / "services/billing/spec/changes/add-invoices/design.md"
    (planned / "src/invoices.py").write_text("def invoice(): ...\n")  # the top level's, not billing's

    def files_check(body):
        design.write_text(f"# Design\n\n## Interfaces\n\n{body}\n")
        _, data = run_json("gate", "design", "--change", "billing:add-invoices", "--no-run")
        return next(c for c in data["checks"] if c["name"] == FILES)

    assert files_check("- `src/invoices.py`: `invoice()`")["details"] == ["src/invoices.py"]
    (planned / "services/billing/src").mkdir()
    (planned / "services/billing/src/invoices.py").write_text("def invoice(): ...\n")
    assert files_check("- `src/invoices.py`: `invoice()`")["ok"]
    assert files_check("- `services/billing/src/invoices.py`: `invoice()`")["ok"]
