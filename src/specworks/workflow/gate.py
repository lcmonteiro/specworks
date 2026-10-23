"""Phase gates: can a change leave a phase? Each gate is a list of named checks.

A skill runs ``specworks gate <phase> --change <ref>`` before suggesting the next
phase. Gates only use facts the CLI can see (specs, tasks, @ac/@req tags); the
skills cover what needs judgement or running the project's tools (for example
that new tests fail for the right reason).
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from ..core.changes import HALVES, PHASES, Change, half_error, set_phase
from ..core.errors import SpecworksError
from ..core.files import read_text
from ..specs.check import DESIGN_FILE
from ..specs.specfile import H2_RE, blank_comments, fenced
from . import checks as c
from .checks import Check, CheckFn, GateContext, passed, run_checks
from .review import CODE_EXTENSIONS
from .validate import validate_change


class GateError(SpecworksError):
    """Raised for a phase without a gate."""


# "## Interfaces", in any case and with any qualifier ("## Interfaces (API)").
INTERFACES_TITLE_RE = re.compile(r"interfaces\b", re.IGNORECASE)
CODE_SPAN_RE = re.compile(r"`([^`\s]+)`")


# @req REQ-FLOW-006
def interfaces_section(change: Change) -> str | None:
    """The text of design.md's Interfaces section without HTML comments, or None if there is none."""
    design = change.path / DESIGN_FILE
    if not design.is_file():
        return None
    lines = blank_comments(read_text(design)).splitlines()
    body: list[str] | None = None  # None until the section starts
    for line, in_fence in zip(lines, fenced(lines), strict=True):
        h2 = None if in_fence else H2_RE.match(line)  # a "## " line in a code fence is an example
        if h2 and body is not None:
            break
        if h2:
            body = [] if INTERFACES_TITLE_RE.match(h2.group("title")) else None
        elif body is not None:
            body.append(line)
    return "\n".join(body).strip() if body is not None else None


# @req REQ-FLOW-006
def interface_files(section: str) -> list[str]:
    """File paths named in code spans (`src/auth/reset.py`, `src/auth/reset.py:ResetService`, `main.py`).

    A name without a folder counts only with a code extension, so `ResetService.request_reset` is not a file.
    """
    paths = []
    for span in CODE_SPAN_RE.findall(section):
        path = re.split(r"[:#(]", span, maxsplit=1)[0]
        name = path.rsplit("/", 1)[-1]
        is_file = "." in name if "/" in path else PurePosixPath(name).suffix.lower() in CODE_EXTENSIONS
        if is_file and path not in paths:
            paths.append(path)
    return paths


# --- design: the API is recorded, its stubs exist and build, nothing broke ---------


# @req REQ-FLOW-006
def interfaces_recorded(ctx: GateContext) -> Check:
    section = interfaces_section(ctx.change)
    return Check(
        'design.md has an Interfaces section (write "None" when the API does not change)',
        bool(section),
        [] if section else ["write the agreed API under ## Interfaces in design.md (specworks instructions design)"],
    )


# @req REQ-FLOW-006
def interface_files_exist(ctx: GateContext) -> Check:
    """A named file counts when it exists inside the change's module, named relative to it or to the workspace root."""
    module_root = ctx.module.root.resolve()

    def in_module(path: str) -> bool:
        found = ((base / path).resolve() for base in (ctx.module.root, ctx.ws.root))
        return any(p.exists() and p.is_relative_to(module_root) for p in found)

    missing = [path for path in interface_files(interfaces_section(ctx.change) or "") if not in_module(path)]
    return Check("every file named under Interfaces exists", not missing, missing)


# @req REQ-FLOW-006
def interface_files_named(ctx: GateContext) -> Check | None:
    section = interfaces_section(ctx.change)
    if not section or interface_files(section) or re.match(r"none\b", section, re.IGNORECASE):
        return None
    return Check(
        "Interfaces names the file of each interface (`src/auth/reset.py`)",
        False,
        ["no file paths found, so the gate cannot check that the stubs exist"],
        blocking=False,
    )


# @req REQ-FLOW-006
def stubs_build(key: str) -> CheckFn:
    def check(ctx: GateContext) -> Check | None:
        return c.command_check(ctx, key, f"the stubs build (commands.{key})") if ctx.has_command(key) else None

    return check


# @req REQ-FLOW-006
def existing_tests_pass(ctx: GateContext) -> Check:
    tests = c.command_check(ctx, "test", "the existing tests still pass with the stubs (commands.test)")
    if tests.ok or not (why := c.own_tests(ctx)):  # the changed files are only computed for a red suite
        return tests
    # The test half has started (or a later cycle reopened the API): this change's
    # own tests are red until the code half makes them pass.
    return c.not_blocking(ctx, tests, f"{why}, which fail until the code half", at=0)


# @req REQ-FLOW-004, REQ-FLOW-006, REQ-FLOW-007, REQ-FLOW-008, REQ-FLOW-011, REQ-FLOW-014
GATE_CHECKS: dict[str, list[CheckFn]] = {
    "specify": [c.specs_valid, c.specs_warnings, c.tasks_written],  # every criterion having a task is one of specs_valid's errors
    "design": [
        c.specs_valid,
        c.specs_warnings,
        c.specs_as_specified,
        interfaces_recorded,
        interface_files_exist,
        interface_files_named,
        stubs_build("build"),
        stubs_build("typecheck"),
        existing_tests_pass,
    ],
    # The two halves of implement: each gate checks only its half (`gate implement` runs both).
    "test": [
        c.specs_valid,
        c.specs_warnings,
        c.specs_as_specified,
        c.half_tasks_done("test"),
        c.acs_have_tests,
        c.no_unknown_tags,
        c.acs_in_test_files,
        c.removed_gone_warning,
    ],
    "code": [
        c.specs_valid,
        c.specs_warnings,
        c.specs_as_specified,
        c.half_tasks_done("code"),
        c.reqs_have_code,
        c.no_unknown_tags,
        c.removed_gone,
        c.code_tests_pass,
    ],
    "review": [
        c.specs_valid,
        c.specs_warnings,
        c.specs_as_specified,
        c.review_written,
        c.review_readable,
        c.review_closed,
        c.reqs_have_code,
        c.acs_have_tests,
        c.no_unknown_tags,
        c.removed_gone,
        c.files_accounted,
        c.diff_base,
        c.modified_tests_changed,
        c.review_tests_pass,
    ],
}
IMPLEMENT = "implement"
GATES = ("specify", "design", "test", "code", IMPLEMENT, "review", "validate")


# @req REQ-FLOW-003
def run_gate(ctx: GateContext, phase: str) -> tuple[bool, list[Check]]:
    if phase not in GATES:
        raise GateError(f"no gate for phase '{phase}' yet; gates exist for: {', '.join(GATES)}")
    if phase == IMPLEMENT:
        return run_implement_gate(ctx)
    checks = validate_change(ctx) if phase == "validate" else run_checks(ctx, GATE_CHECKS[phase])
    return passed(checks), checks


# @req REQ-FLOW-014
def run_implement_gate(ctx: GateContext) -> tuple[bool, list[Check]]:
    """The test gate, then (once it passes) the code gate, each check named after its half."""
    checks: list[Check] = []
    for half in HALVES:
        ok, half_checks = run_gate(ctx, half)
        for check in half_checks:
            check.name = f"{half}: {check.name}"
        checks += half_checks
        if not ok:
            return False, checks
    return True, checks


# @req REQ-FLOW-014
def gates_to_start(current: str, phase: str) -> list[str]:
    """Gates that must pass before a change in ``current`` starts ``phase``.

    Moving forward, every phase left behind must be finished (its gate, when it
    has one). Re-entering a phase, or going back to one for rework, needs only
    the gate of the phase just before it.
    """
    if phase in HALVES:
        raise GateError(f"cannot start {half_error(phase)}; start `implement`")
    if phase not in PHASES or phase == "done":
        startable = ", ".join(p for p in PHASES if p != "done")
        raise GateError(f"cannot start '{phase}'; phases are {startable} (`specworks close` finishes a change)")
    target = PHASES.index(phase)
    first = PHASES.index(current) if PHASES.index(current) < target else target - 1
    gates = [p for p in PHASES[max(first, 0) : target] if p in GATES]
    return [g for p in gates for g in (HALVES if p == IMPLEMENT else (p,))]  # implement's gate is its two halves


# @req REQ-FLOW-014, REQ-FLOW-005
def start_phase(ctx: GateContext, phase: str) -> tuple[bool, list[tuple[str, list[Check]]]]:
    """Run the gates ``phase`` depends on, in order, and move the change to it if they all pass.

    Stops at the first gate that does not pass; returns whether the change
    moved and each gate that ran with its checks.
    """
    ran: list[tuple[str, list[Check]]] = []
    for gate in gates_to_start(ctx.change.phase, phase):
        ok, checks = run_gate(ctx, gate)
        ran.append((gate, checks))
        if not ok:
            return False, ran
        if gate == "specify":
            # The specs are agreed as they are now; later gates warn when they change (saved with the phase).
            ctx.change.specified = ctx.analysis.specs.fingerprints()
    set_phase(ctx.change, phase)
    return True, ran
