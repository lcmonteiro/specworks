"""Phase gates: can a change leave a phase? Each gate is a list of named checks.

A skill runs ``specworks gate <phase> --change <ref>`` before suggesting the next
phase. Gates only use facts the CLI can see (specs, tasks, @ac/@req tags); the
skills cover what needs judgement or running the project's tools (for example
that new tests fail for the right reason).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePosixPath

from ..core.changes import PHASES, Change, set_phase
from ..core.workspace import Module, Workspace
from ..specs.check import ChangeSpecs, check_change
from ..specs.trace import build_matrix, gaps, scan_tags, unknown_tags
from .checks import Check, accounted_check, change_ids, command_check, tests_pass
from .review import CODE_EXTENSIONS, REVIEW_FILE, read_review, review_change
from .validate import validate_change


class GateError(Exception):
    """Raised for a phase without a gate."""


@dataclass
class GateContext:
    ws: Workspace
    module: Module
    change: Change
    run_tests: bool = True  # False: --no-run, the project's commands are reported as not run
    base: str | None = None  # review / validate: branch to diff against
    allow_open: bool = False  # review: open findings do not fail the gate (inside a build)


def _spec_checks(ctx: GateContext) -> tuple[ChangeSpecs, list[Check]]:
    specs, issues = check_change(ctx.ws, ctx.change)
    errors = [str(i) for i in issues if i.level == "error"]
    return specs, [Check("specs and tasks are valid (specworks check)", not errors, errors)]


def _specify(ctx: GateContext) -> list[Check]:
    specs, checks = _spec_checks(ctx)
    checks.append(
        Check(
            "tasks.md is written",
            specs.tasks_found,
            [] if specs.tasks_found else ["write tasks.md (specworks instructions tasks)"],
        )
    )
    if not ctx.change.skip_specs:
        missing = gaps(build_matrix(specs, []))["acWithoutTasks"]
        checks.append(Check("every acceptance criterion has a task", not missing, missing))
    return checks


INTERFACES_RE = re.compile(r"^## Interfaces[ \t]*\n(?P<body>.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
CODE_SPAN_RE = re.compile(r"`([^`\s]+)`")


def interfaces_section(change: Change) -> str | None:
    """The text of design.md's Interfaces section without HTML comments, or None if there is none."""
    design = change.path / "design.md"
    if not design.is_file():
        return None
    match = INTERFACES_RE.search(design.read_text(encoding="utf-8"))
    return re.sub(r"<!--.*?-->", "", match.group("body"), flags=re.DOTALL).strip() if match else None


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


def _design(ctx: GateContext) -> list[Check]:
    ws, module, change = ctx.ws, ctx.module, ctx.change
    specs, checks = _spec_checks(ctx)
    section = interfaces_section(change)
    checks.append(
        Check(
            'design.md has an Interfaces section (write "None" when the API does not change)',
            bool(section),
            [] if section else ["write the agreed API under ## Interfaces in design.md (specworks instructions design)"],
        )
    )
    files = interface_files(section or "")
    missing = [path for path in files if not (module.root / path).exists() and not (ws.root / path).exists()]
    checks.append(Check("every file named under Interfaces exists", not missing, missing))
    if section and not files and not re.match(r"none\b", section, re.IGNORECASE):
        checks.append(
            Check(
                "Interfaces names the file of each interface (`src/auth/reset.py`)",
                False,
                ["no file paths found, so the gate cannot check that the stubs exist"],
                blocking=False,
            )
        )
    for key in ("build", "typecheck"):
        if ws.commands(module).get(key):
            checks.append(command_check(ws, module, key, f"the stubs build (commands.{key})", ctx.run_tests))
    tests = command_check(ws, module, "test", "the existing tests still pass with the stubs (commands.test)", ctx.run_tests)
    ids = change_ids(specs)
    ran = ctx.run_tests and bool(ws.commands(module).get("test"))  # a missing command still blocks
    if ran and not tests.ok and any(t.kind == "ac" and t.is_test and t.id in ids for t in scan_tags(ws)):
        # The test phase has started (or a later cycle reopened the API): this change's
        # own tests are red until the code phase, whose gate requires a green suite.
        tests.blocking = False
        tests.details.insert(0, "not blocking: this change already has @ac tests, which fail until the code phase")
    checks.append(tests)
    return checks


def _test(ctx: GateContext) -> list[Check]:
    specs, checks = _spec_checks(ctx)
    tags = scan_tags(ctx.ws)
    found = gaps(build_matrix(specs, tags))
    stray = unknown_tags(specs, tags)
    ids = change_ids(specs)
    misplaced = [t for t in tags if t.kind == "ac" and not t.is_test and t.id in ids]
    return checks + [
        Check("every acceptance criterion has a test (@ac tag in a test file)", not found["acWithoutTests"], found["acWithoutTests"]),
        Check("no tag refers to an unknown requirement or criterion", not stray, [f"{t.id} at {t.where}" for t in stray]),
        Check(
            "@ac tags are in test files (configure test_globs if your tests live elsewhere)",
            not misplaced,
            [f"{t.id} at {t.where}" for t in misplaced],
            blocking=False,
        ),
        Check("removed requirements are no longer tagged", not found["removedStillTagged"], found["removedStillTagged"], blocking=False),
    ]


def _code(ctx: GateContext) -> list[Check]:
    specs, checks = _spec_checks(ctx)
    pending = [f"{t.num} {t.text}" for t in specs.tasks if not t.done]
    tags = scan_tags(ctx.ws)
    found = gaps(build_matrix(specs, tags))
    stray = unknown_tags(specs, tags)
    return checks + [
        Check("every task is done (specworks task list --pending)", specs.tasks_found and not pending, pending),
        Check("every requirement has code (@req tag)", not found["reqWithoutCode"], found["reqWithoutCode"]),
        Check("every acceptance criterion still has a test (@ac tag)", not found["acWithoutTests"], found["acWithoutTests"]),
        Check("no tag refers to an unknown requirement or criterion", not stray, [f"{t.id} at {t.where}" for t in stray]),
        Check("removed requirements are gone from tests and code", not found["removedStillTagged"], found["removedStillTagged"]),
        tests_pass(ctx.ws, ctx.module, ctx.run_tests),
    ]


def _review(ctx: GateContext) -> list[Check]:
    _, report = review_change(ctx.ws, ctx.change, ctx.base)
    found = report.findings()
    review = read_review(ctx.change)
    open_findings = [f"{f.id} {f.text}" for f in review.open]
    return [
        Check("specs and tasks are valid (specworks check)", not report.spec_errors, report.spec_errors),
        Check(f"{REVIEW_FILE} is written", review.exists, [] if review.exists else ["write it (specworks instructions review)"]),
        # In a build, open findings are the hand-off to the next cycle (`specworks cycle`), not a failure.
        Check(f"every finding in {REVIEW_FILE} is readable (- [ ] R<n> ...)", not review.problems, review.problems),
        Check(f"no open finding in {REVIEW_FILE}", review.exists and not open_findings, open_findings, blocking=not ctx.allow_open),
        Check("every requirement has code (@req tag)", not found["reqWithoutCode"], found["reqWithoutCode"]),
        Check("every acceptance criterion has a test (@ac tag)", not found["acWithoutTests"], found["acWithoutTests"]),
        Check("no tag refers to an unknown requirement or criterion", not found["unknownTags"], found["unknownTags"]),
        Check("removed requirements are gone from tests and code", not found["removedStillTagged"], found["removedStillTagged"]),
        accounted_check(report, review),
        tests_pass(ctx.ws, ctx.module, ctx.run_tests),
    ]


def _validate(ctx: GateContext) -> list[Check]:
    return validate_change(ctx.ws, ctx.module, ctx.change, ctx.run_tests, ctx.base)


GATE_CHECKS: dict[str, Callable[[GateContext], list[Check]]] = {
    "specify": _specify,
    "design": _design,
    "test": _test,
    "code": _code,
    "review": _review,
    "validate": _validate,
}
GATES = tuple(GATE_CHECKS)


def run_gate(ctx: GateContext, phase: str) -> tuple[bool, list[Check]]:
    if phase not in GATE_CHECKS:
        raise GateError(f"no gate for phase '{phase}' yet; gates exist for: {', '.join(GATES)}")
    checks = GATE_CHECKS[phase](ctx)
    return all(c.ok for c in checks if c.blocking), checks


def gates_to_start(current: str, phase: str) -> list[str]:
    """Gates that must pass before a change in ``current`` starts ``phase``.

    Moving forward, every phase left behind must be finished (its gate, when it
    has one). Re-entering a phase, or going back to one for rework, needs only
    the gate of the phase just before it.
    """
    if phase not in PHASES or phase == "done":
        startable = ", ".join(p for p in PHASES if p != "done")
        raise GateError(f"cannot start '{phase}'; phases are {startable} (`specworks close` finishes a change)")
    target = PHASES.index(phase)
    first = PHASES.index(current) if PHASES.index(current) < target else target - 1
    return [p for p in PHASES[max(first, 0) : target] if p in GATE_CHECKS]


def start_phase(ctx: GateContext, phase: str) -> tuple[bool, list[tuple[str, list[Check]]]]:
    """Run the gates ``phase`` depends on, in order, and move the change to it if they all pass.

    Stops at the first gate that does not pass; returns whether the change
    moved and each gate that ran with its checks.
    """
    ran: list[tuple[str, list[Check]]] = []
    for gate in gates_to_start(ctx.change.phase, phase):
        passed, checks = run_gate(ctx, gate)
        ran.append((gate, checks))
        if not passed:
            return False, ran
    set_phase(ctx.change, phase)
    return True, ran
