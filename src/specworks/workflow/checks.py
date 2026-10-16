"""The checks behind the phase gates and validate, each defined once.

A check is a function of a ``GateContext``: what it reads (specs, tags, git, review.md)
is computed on first use and shared by every check of the same run. A check returns
``None`` when it does not apply. Gates and validate are lists of these checks.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from functools import cached_property

from ..core.changes import Change
from ..core.runner import CommandError, cached_run
from ..core.workspace import Module, Workspace
from ..specs.tasks import TASKS_FILE
from ..specs.trace import Analysis
from .review import REVIEW_FILE, ReviewDoc, ReviewReport, read_review, review_change


@dataclass
class Check:
    name: str
    ok: bool
    details: list[str] = field(default_factory=list)
    blocking: bool = True
    group: str = ""  # validate: completeness / correctness / coherence
    fix: str = ""  # validate: the phase skill that fixes a failure

    @property
    def mark(self) -> str:
        return "ok  " if self.ok else ("FAIL" if self.blocking else "warn")

    def to_dict(self) -> dict:
        data = {"name": self.name, "ok": self.ok, "blocking": self.blocking, "details": self.details}
        if self.group:
            data["group"] = self.group
        if self.fix:
            data["fix"] = self.fix
        return data


@dataclass
class GateContext:
    ws: Workspace
    module: Module
    change: Change
    run_tests: bool = True  # False: --no-run, the project's commands are reported as not run
    base: str | None = None  # review / validate: branch to diff against
    allow_open: bool = False  # review: open findings do not fail the gate (inside a build)

    @cached_property
    def analysis(self) -> Analysis:
        return Analysis(self.ws, self.change)

    @cached_property
    def report(self) -> ReviewReport:
        return review_change(self.analysis, self.base)

    @cached_property
    def review(self) -> ReviewDoc:
        return read_review(self.change)

    def has_command(self, key: str) -> bool:
        return bool(self.ws.commands(self.module).get(key))


CheckFn = Callable[[GateContext], "Check | None"]


def passed(checks: list[Check]) -> bool:
    """A gate passes when none of its blocking checks fails; warnings never block."""
    return all(c.ok for c in checks if c.blocking)


def run_checks(ctx: GateContext, checks: Iterable[CheckFn]) -> list[Check]:
    return [c for check in checks if (c := check(ctx)) is not None]


def _listed(name: str, missing: list[str], blocking: bool = True) -> Check:
    """Passes when nothing is listed; the listed items are the details."""
    return Check(name, not missing, missing, blocking=blocking)


# --- specs and tasks -----------------------------------------------------------


def specs_valid(ctx: GateContext) -> Check:
    return _listed("specs and tasks are valid (specworks check)", ctx.analysis.spec_errors)


def specs_warnings(ctx: GateContext) -> Check:
    """`specworks check`'s warnings, shown in every gate and validate without blocking."""
    return _listed("specworks check has no warnings", ctx.analysis.spec_warnings, blocking=False)


def tasks_written(ctx: GateContext) -> Check:
    found = ctx.analysis.specs.tasks_found
    return Check(f"{TASKS_FILE} is written", found, [] if found else [f"write {TASKS_FILE} (specworks instructions tasks)"])


def tasks_done(ctx: GateContext) -> Check:
    specs = ctx.analysis.specs
    pending = [f"{t.num} {t.text}" for t in specs.tasks if not t.done]
    return Check("every task is done (specworks task list --pending)", specs.tasks_found and not pending, pending)


# --- tags ------------------------------------------------------------------------


def _gap(name: str, key: str, blocking: bool = True) -> CheckFn:
    """A check that passes when the traceability gap ``key`` (trace.gaps) is empty."""
    return lambda ctx: _listed(name, ctx.analysis.gaps[key], blocking)


reqs_have_code = _gap("every requirement has code (@req tag)", "reqWithoutCode")
acs_have_tests = _gap("every acceptance criterion has a test (@ac tag)", "acWithoutTests")
removed_gone = _gap("removed requirements are gone from tests and code", "removedStillTagged")
# Before the code phase, the code of a removed requirement may still be there.
removed_gone_warning = _gap("removed requirements are gone from tests and code", "removedStillTagged", blocking=False)


def no_unknown_tags(ctx: GateContext) -> Check:
    return _listed("no tag refers to an unknown requirement or criterion", [t.at for t in ctx.analysis.unknown_tags])


def acs_in_test_files(ctx: GateContext) -> Check:
    ids_ = change_ids(ctx)
    misplaced = [t.at for t in ctx.analysis.tags if t.kind == "ac" and not t.is_test and t.id in ids_]
    return _listed("@ac tags are in test files (configure test_globs if your tests live elsewhere)", misplaced, blocking=False)


def change_ids(ctx: GateContext) -> set[str]:
    """Every requirement and acceptance-criterion ID in the change's delta specs."""
    return {i for d in ctx.analysis.specs.deltas for i in d.doc.ids()}


# --- review.md -----------------------------------------------------------------


def review_written(ctx: GateContext) -> Check:
    exists = ctx.review.exists
    return Check(f"{REVIEW_FILE} is written", exists, [] if exists else [f"write {REVIEW_FILE} (specworks instructions review)"])


def review_readable(ctx: GateContext) -> Check:
    """A checkbox the parser cannot read may be an open finding, so it never passes silently."""
    return _listed(f"every finding in {REVIEW_FILE} is readable (- [ ] R<n> ...)", ctx.review.problems)


def review_closed(ctx: GateContext) -> Check:
    """In a build (--allow-open), open findings are the hand-off to the next cycle (`specworks cycle`), not a failure."""
    open_findings = [f"{f.id} {f.text}" for f in ctx.review.open]
    return Check(f"no open finding in {REVIEW_FILE}", ctx.review.exists and not open_findings, open_findings, blocking=not ctx.allow_open)


def files_accounted(ctx: GateContext) -> Check:
    """Every changed file without tags is listed under "Changed files without tags" in review.md."""
    report = ctx.report
    if report.changed is None:
        return Check("changed files without tags are accounted for", False, [report.note], blocking=False)
    missing = [path for path in report.untraced_source + report.untraced_tests if not ctx.review.accounts_for(path)]
    return _listed(f"changed files without tags are accounted for in {REVIEW_FILE} (base {report.base})", missing)


# --- the project's commands ---------------------------------------------------------


def command_check(ctx: GateContext, key: str, name: str, optional: bool = False) -> Check:
    """Run ``commands.<key>``; ``optional`` commands pass (as a warning) when not configured."""
    if optional and not ctx.has_command(key):
        return Check(name, True, ["not configured"], blocking=False)
    if not ctx.run_tests:
        return Check(name, False, [f"not run (--no-run); run `specworks run {key}`"], blocking=False)
    try:
        result = cached_run(ctx.ws, ctx.module, key)
    except CommandError as exc:
        return Check(name, False, [str(exc)])
    reused = f", same code as the run at {result.cached_at}" if result.cached_at else ""
    details = [f"$ {result.command}  (in {result.cwd}, exit {result.exit_code}{reused})"]
    return Check(name, result.ok, details if result.ok else details + result.tail())


def tests_pass(ctx: GateContext) -> Check:
    return command_check(ctx, "test", "the test suite passes (commands.test)")


def optional_command(key: str, name: str) -> CheckFn:
    return lambda ctx: command_check(ctx, key, name, optional=True)
