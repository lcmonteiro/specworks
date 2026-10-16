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

from ..core.changes import Change
from ..core.errors import SpecworksError
from ..core.workspace import Module, Workspace
from ..specs.check import ChangeSpecs, check_change
from ..specs.trace import scan_tags, trace_change
from .checks import Check, change_ids, command_check, reviewed_checks, spec_check, tag_checks, tests_pass
from .review import read_review, review_change
from .validate import validate_change


class GateError(SpecworksError):
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
    return specs, [spec_check([str(i) for i in issues if i.level == "error"])]


def _specify(ctx: GateContext) -> list[Check]:
    specs, checks = _spec_checks(ctx)
    checks.append(
        Check(
            "tasks.md is written",
            specs.tasks_found,
            [] if specs.tasks_found else ["write tasks.md (specworks instructions tasks)"],
        )
    )
    return checks  # every criterion having a task is already one of `specworks check`'s errors


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
    """File paths named in code spans (`src/auth/reset.py`, `src/auth/reset.py:ResetService`)."""
    paths = []
    for span in CODE_SPAN_RE.findall(section):
        path = re.split(r"[:#(]", span, maxsplit=1)[0]
        if "/" in path and "." in path.rsplit("/", 1)[-1] and path not in paths:
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
    trace = trace_change(ctx.ws, ctx.change)
    found = trace.findings()
    ids = change_ids(trace.specs)
    misplaced = [t for t in trace.tags if t.kind == "ac" and not t.is_test and t.id in ids]
    return [
        spec_check(trace.spec_errors),
        Check("every acceptance criterion has a test (@ac tag in a test file)", not found["acWithoutTests"], found["acWithoutTests"]),
        Check("no tag refers to an unknown requirement or criterion", not found["unknownTags"], found["unknownTags"]),
        Check(
            "@ac tags are in test files (configure test_globs if your tests live elsewhere)",
            not misplaced,
            [f"{t.id} at {t.where}" for t in misplaced],
            blocking=False,
        ),
        Check("removed requirements are no longer tagged", not found["removedStillTagged"], found["removedStillTagged"], blocking=False),
    ]


def _code(ctx: GateContext) -> list[Check]:
    trace = trace_change(ctx.ws, ctx.change)
    specs = trace.specs
    pending = [f"{t.num} {t.text}" for t in specs.tasks if not t.done]
    return [
        spec_check(trace.spec_errors),
        Check("every task is done (specworks task list --pending)", specs.tasks_found and not pending, pending),
        *tag_checks(trace.findings()),
        tests_pass(ctx.ws, ctx.module, ctx.run_tests),
    ]


def _review(ctx: GateContext) -> list[Check]:
    report = review_change(ctx.ws, ctx.change, ctx.base)
    return reviewed_checks(ctx.ws, ctx.module, report, read_review(ctx.change), ctx.run_tests, ctx.allow_open)


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
