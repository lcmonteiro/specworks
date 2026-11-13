"""
The checks behind the phase gates and validate, each defined once.

A check is a function of a ``GateContext``: what it reads (specs, tags, git, review.md)
is computed on first use and shared by every check of the same run. A check returns
``None`` when it does not apply. Gates and validate are lists of these checks.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from specworks.core.changes import Change
from specworks.core.config import SCOPED_TEST_KEY
from specworks.core.runner import CommandError, cached_run, run_scoped
from specworks.core.workspace import Module, Workspace
from specworks.specs.tasks import TASKS_FILE
from specworks.specs.trace import Analysis
from specworks.workflow.artifacts import CheckArtifact, check_artifact, load_artifacts
from specworks.workflow.findings import FindingsDoc, read_findings
from specworks.workflow.review import ReviewReport, review_change

REVIEW_ARTIFACT = check_artifact("review")
REVIEW_FILE = REVIEW_ARTIFACT.file


@dataclass
class Check:
    name: str
    ok: bool
    details: list[str] = field(default_factory=list)
    blocking: bool = True
    group: str = ""  # validate: completeness / correctness / coherence
    fix: str = ""  # validate: the phase skill that fixes a failure
    key: str = ""  # validate: the name of the check function, stable when the name shows a base (REQ-FLOW-019)

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
    reuse_runs: bool = True  # False: run each project command once for real (the real close, --fresh), never an earlier result
    ran: set[str] = field(default_factory=set)  # commands already run for real in this invocation
    read: dict[str, FindingsDoc] = field(default_factory=dict)  # each check artifact's findings, by id, once read

    @cached_property
    def analysis(self) -> Analysis:
        return Analysis(self.ws, self.change)

    @cached_property
    def report(self) -> ReviewReport:
        return review_change(self.analysis, self.base)

    @property
    def review(self) -> FindingsDoc:
        """
        review.md's findings.
        """
        return self.findings(REVIEW_ARTIFACT)

    # @req REQ-FLOW-011, REQ-FLOW-013
    def findings(self, artifact: CheckArtifact) -> FindingsDoc:
        """
        A check artifact's findings, read once per run and artifact (``read.clear()`` reads them again).

        Implements REQ-FLOW-011, REQ-FLOW-013.
        """
        if artifact.id not in self.read:
            self.read[artifact.id] = read_findings(self.change, artifact)
        return self.read[artifact.id]

    @cached_property
    def test_plan(self) -> TestPlan:
        """
        The tests the review gate runs (``test_plan``), computed once per run.
        """
        return test_plan(self)

    def has_command(self, key: str) -> bool:
        return bool(self.ws.commands(self.module).get(key))


CheckFn = Callable[[GateContext], "Check | None"]


# @req REQ-FLOW-003
def passed(checks: list[Check]) -> bool:
    """
    A gate passes when none of its blocking checks fails; warnings never block.
    """
    return all(c.ok for c in checks if c.blocking)


# @req REQ-FLOW-003
def run_checks(ctx: GateContext, checks: Iterable[CheckFn]) -> list[Check]:
    return [c for check in checks if (c := check(ctx)) is not None]


def _listed(name: str, missing: list[str], blocking: bool = True) -> Check:
    """
    Passes when nothing is listed; the listed items are the details.
    """
    return Check(name, not missing, missing, blocking=blocking)


# --- specs and tasks -----------------------------------------------------------


# @req REQ-FLOW-003
def specs_valid(ctx: GateContext) -> Check:
    return _listed("specs and tasks are valid (specworks check)", ctx.analysis.spec_errors)


# @req REQ-FLOW-003
def specs_warnings(ctx: GateContext) -> Check:
    """
    `specworks check`'s warnings, shown in every gate and validate without blocking.
    """
    return _listed("specworks check has no warnings", ctx.analysis.spec_warnings, blocking=False)


# @req REQ-FLOW-004
def tasks_written(ctx: GateContext) -> Check:
    found = ctx.analysis.specs.tasks_found
    return Check(f"{TASKS_FILE} is written", found, [] if found else [f"write {TASKS_FILE} (specworks instructions tasks)"])


# @req REQ-FLOW-007, REQ-FLOW-008
def half_tasks_done(half: str) -> CheckFn:
    """
    A check that every task of ``half`` (``test`` or ``code``) is done, listing only that half's open tasks.
    """

    def check(ctx: GateContext) -> Check:
        specs = ctx.analysis.specs
        pending = [f"{t.num} {t.text}" for t in specs.tasks if t.half == half and not t.done]
        return Check(f"every [{half}] task is done (specworks task list --pending)", specs.tasks_found and not pending, pending)

    return _named(check, f"{half}_tasks_done")


# @req REQ-FLOW-013
def unmarked_tasks_done(ctx: GateContext) -> Check:
    """
    Every task with neither a ``[test]`` nor a ``[code]`` marker (design's stub tasks) is done, listing the open ones.
    """
    specs = ctx.analysis.specs
    pending = [f"{t.num} {t.text}" for t in specs.tasks if not t.half and not t.done]
    return Check("every task with no [test] or [code] marker is done (specworks task list --pending)", specs.tasks_found and not pending, pending)


# @req REQ-FLOW-005
def specs_as_specified(ctx: GateContext) -> Check | None:
    """
    The delta specs are the ones `gate specify` passed with when `start` last left specify (not checked without one).
    """
    agreed = ctx.change.specified
    if not agreed:
        return None
    now = ctx.analysis.specs.fingerprints()
    details = [f"{i} changed" for i in agreed if i in now and now[i] != agreed[i]]
    details += [f"{i} added" for i in now if i not in agreed] + [f"{i} dropped" for i in agreed if i not in now]
    if details:
        ref = ctx.module.qualify(ctx.change.name)
        details.append(f"if that is intended, `specworks start design --change {ref}` re-checks specify and accepts them; "
                       "the tests and code then follow the new specs")
    return Check("the specs are the ones agreed when specify passed", not details, details, blocking=False)


# --- tags ------------------------------------------------------------------------


def _named(check: CheckFn, name: str) -> CheckFn:
    """
    ``check`` named ``name``: the key validate links its findings to (REQ-FLOW-019).
    """
    check.__name__ = check.__qualname__ = name
    return check


def _gap(fn_name: str, name: str, key: str, blocking: bool = True) -> CheckFn:
    """
    A check named ``fn_name`` that passes when the traceability gap ``key`` (trace.gaps) is empty.
    """
    return _named(lambda ctx: _listed(name, ctx.analysis.gaps[key], blocking), fn_name)


reqs_have_code = _gap("reqs_have_code", "every requirement has code (@req tag)", "reqWithoutCode")
acs_have_tests = _gap("acs_have_tests", "every acceptance criterion has a test (@ac tag)", "acWithoutTests")
removed_gone = _gap("removed_gone", "removed requirements and criteria are gone from tests and code", "removedStillTagged")
# Before the code half is done, the code of a removed requirement (or criterion) may still be there.
removed_gone_warning = _gap("removed_gone_warning", "removed requirements and criteria are gone from tests and code", "removedStillTagged", blocking=False)


# @req REQ-FLOW-007
def no_unknown_tags(ctx: GateContext) -> Check:
    return _listed("no tag refers to an unknown requirement or criterion", [t.at for t in ctx.analysis.unknown_tags])


# @req REQ-FLOW-007
def acs_in_test_files(ctx: GateContext) -> Check:
    ids_ = change_ids(ctx)
    misplaced = [t.at for t in ctx.analysis.tags if t.kind == "ac" and not t.is_test and t.id in ids_]
    return _listed("@ac tags are in test files (configure test_globs if your tests live elsewhere)", misplaced, blocking=False)


def change_ids(ctx: GateContext) -> set[str]:
    """
    Every requirement and acceptance-criterion ID in the change's delta specs.
    """
    return {i for d in ctx.analysis.specs.deltas for i in d.doc.ids()}


# --- review.md -----------------------------------------------------------------


# @req REQ-FLOW-011
def review_written(ctx: GateContext) -> Check:
    exists = ctx.review.exists
    return Check(f"{REVIEW_FILE} is written", exists, [] if exists else [f"write {REVIEW_FILE} (specworks instructions review)"])


def artifact_readable(artifact: CheckArtifact) -> CheckFn:
    """
    The check that every finding in the check artifact is readable (``- [ ] <letter><n> ...``): a checkbox the parser
    cannot read may be an open finding, so it never passes silently. Review's keeps its name and details.

    Implements REQ-FLOW-010, REQ-FLOW-011, REQ-FLOW-013.
    """

    # @req REQ-FLOW-010, REQ-FLOW-013
    def readable(ctx: GateContext) -> Check:
        return _listed(f"every finding in {artifact.file} is readable (- [ ] {artifact.letter}<n> ...)", ctx.findings(artifact).problems)

    readable.__name__ = f"{artifact.id}_readable"
    return readable


def artifact_closed(artifact: CheckArtifact) -> CheckFn:
    """
    The check that the check artifact has no open finding. In a build (--allow-open), open findings are the hand-off
    to the next cycle (`specworks cycle`), not a failure. Review's keeps its name and details.

    Implements REQ-FLOW-011, REQ-FLOW-013.
    """
    # A missing file fails only when the artifact is required (review.md); validation.md is optional.
    required = not load_artifacts()[artifact.id].optional

    # @req REQ-FLOW-011, REQ-FLOW-013
    def closed(ctx: GateContext) -> Check:
        doc = ctx.findings(artifact)
        open_findings = [f"{f.id} {f.text}" for f in doc.open]
        written = doc.exists or not required
        return Check(f"no open finding in {artifact.file}", written and not open_findings, open_findings, blocking=not ctx.allow_open)

    closed.__name__ = f"{artifact.id}_closed"
    return closed


# @req REQ-FLOW-011
def files_accounted(ctx: GateContext) -> Check:
    """
    Every changed file without tags, and every deleted source or test file, is listed under "Changed files without tags" in review.md.
    """
    report = ctx.report
    if report.changed is None:
        return Check("changed files without tags are accounted for", False, [report.note], blocking=False)
    unseen = report.untraced_source + report.untraced_tests + report.deleted_files
    missing = [path for path in unseen if not ctx.review.accounts_for(path)]
    return _listed(f"changed files without tags are accounted for in {REVIEW_FILE} (base {report.since})", missing)


# @req REQ-FLOW-011
def modified_tests_changed(ctx: GateContext) -> Check | None:
    """
    Each MODIFIED requirement whose behaviour changes has a test file changed on the branch: old tests only check the old one.
    """
    report = ctx.report
    if report.changed is None:
        return None
    modified = [(d, r) for d, r in ctx.analysis.specs.requirements("MODIFIED") if d.behaviour_changed(r)]
    if not modified:
        return None
    changed = {f.path for f in report.changed}
    stale = []
    for _, req in modified:
        acs = {sc.id for sc in req.scenarios if sc.id}
        files = sorted({t.file for t in ctx.analysis.tags if t.is_test and t.id in acs})
        if files and not changed.intersection(files):
            stale.append(f"{req.id}: none of its tests changed ({', '.join(files)}); make sure they check the new behaviour")
    return _listed("the tests of each MODIFIED requirement changed with it", stale, blocking=False)


# @req REQ-FLOW-011
def diff_base(ctx: GateContext) -> Check | None:
    """
    Warns when the changed files may be incomplete: HEAD is on the base branch and nothing marks where the change started.
    """
    report = ctx.report
    return Check("the change's commits are compared with its base", False, [report.note], blocking=False) if report.on_base else None


# --- the project's commands ---------------------------------------------------------


# @req REQ-FLOW-003
def command_check(ctx: GateContext, key: str, name: str, optional: bool = False) -> Check:
    """
    Run ``commands.<key>``; ``optional`` commands pass (as a warning) when not configured.
    """
    if optional and not ctx.has_command(key):
        return Check(name, True, ["not configured"], blocking=False)
    if not ctx.run_tests:
        return Check(name, False, [f"not run (--no-run); run `specworks run {key}`"], blocking=False)
    try:
        result = cached_run(ctx.ws, ctx.module, key, reuse=ctx.reuse_runs or key in ctx.ran)
        ctx.ran.add(key)
    except CommandError as exc:
        return Check(name, False, [str(exc)])
    reused = f", same code as the run at {result.cached_at}" if result.cached_at else ""
    details = [f"$ {result.command}  (in {result.cwd}, exit {result.exit_code}{reused})"]
    return Check(name, result.ok, details if result.ok else details + result.tail())


# @req REQ-FLOW-011
def tests_pass(ctx: GateContext) -> Check:
    return command_check(ctx, "test", "the test suite passes (commands.test)")


def not_blocking(ctx: GateContext, tests: Check, why: str, at: int = 1, configured: bool | None = None) -> Check:
    """
    A failing run of the suite (not a missing command) as a warning, saying why at ``at`` in the details (after the command line).

    ``configured``: whether the command that ran is configured; by default, whether ``commands.test`` is.
    """
    if ctx.run_tests and (ctx.has_command("test") if configured is None else configured) and not tests.ok:
        tests.blocking = False
        tests.details.insert(at, f"not blocking: {why}")
    return tests


@dataclass
class TestPlan:
    """
    What the review gate's test check runs.

    ``full``: the whole suite (``commands.test``); otherwise ``runs``, one per module (in workspace order)
    with its touched capabilities' test folders, sorted, for its ``commands.test_scoped``.
    ``missing``: the touched test folders that do not exist, relative to the workspace root.
    Implements REQ-FLOW-017.
    """

    full: bool
    runs: list[tuple[Module, list[Path]]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


# @req REQ-FLOW-017
def test_plan(ctx: GateContext) -> TestPlan:
    """
    The touched capabilities' test runs, or the full suite (see ``TestPlan``). Implements REQ-FLOW-017.

    Touched: every delta's capability, and every capability whose code path or test folder holds a
    changed file (deleted ones included; without git, only the deltas count).
    """
    ws = ctx.ws
    touched: dict[tuple[str, str], tuple[Module, Path]] = {}
    for delta in ctx.analysis.specs.deltas:
        module, cap = delta.cap.module, delta.cap.capability
        folder = cap.tests_path(module.root, module.config.tests_dir) if cap else module.root / module.config.tests_dir / delta.cap.name
        touched[(module.name, delta.cap.name)] = (module, folder)
    changed = [(ws.root / f.path).resolve() for f in ctx.report.changed or []]
    for module, cap in ws.capabilities():
        folder = cap.tests_path(module.root, module.config.tests_dir)
        owned = ((module.root / cap.path).resolve(), folder.resolve())
        if any(path.is_relative_to(base) for path in changed for base in owned):
            touched.setdefault((module.name, cap.name), (module, folder))
    if not touched or any(not ws.commands(module).get(SCOPED_TEST_KEY) for module, _ in touched.values()):
        return TestPlan(full=True)
    missing = sorted({ws.rel(folder) for _, folder in touched.values() if not folder.is_dir()})
    if missing:
        return TestPlan(full=True, missing=missing)
    runs = []
    for module in ws.modules():
        folders = sorted({folder for m, folder in touched.values() if m is module})
        if folders:
            runs.append((module, folders))
    return TestPlan(full=False, runs=runs)


# @req REQ-FLOW-017
def test_folders_exist(ctx: GateContext) -> Check | None:
    """
    A warning naming each touched test folder that does not exist (the full suite runs instead); ``None``
    when none is missing or ``commands.test_scoped`` is not configured. Implements REQ-FLOW-017.
    """
    missing = ctx.test_plan.missing  # only computed when every touched capability's module has test_scoped
    if not missing:
        return None
    details = [f"{folder} does not exist" for folder in missing] + ["the full suite (commands.test) runs instead"]
    return Check("the touched capabilities' test folders exist", False, details, blocking=False)


SCOPED_TESTS = f"the touched capabilities' tests pass (commands.{SCOPED_TEST_KEY})"


# @req REQ-FLOW-017
def scoped_tests_pass(ctx: GateContext, plan: TestPlan) -> Check:
    """
    One run of ``commands.test_scoped`` per module of ``plan``, passing only when every run passes.
    """
    if not ctx.run_tests:
        return Check(SCOPED_TESTS, False, ["not run (--no-run); `specworks gate review` runs them"], blocking=False)
    details: list[str] = []
    ok = True
    for module, folders in plan.runs:
        try:
            ran = f"{SCOPED_TEST_KEY} {module.label} {[str(f) for f in folders]}"
            result = run_scoped(ctx.ws, module, folders, reuse=ctx.reuse_runs or ran in ctx.ran)
            ctx.ran.add(ran)
        except CommandError as exc:
            return Check(SCOPED_TESTS, False, [str(exc)])
        reused = f", same code as the run at {result.cached_at}" if result.cached_at else ""
        details.append(f"$ {result.command}  (in {result.cwd}, exit {result.exit_code}{reused})")
        if not result.ok:
            ok = False
            details += result.tail()
    return Check(SCOPED_TESTS, ok, details)


# @req REQ-FLOW-011, REQ-FLOW-017
def review_tests_pass(ctx: GateContext) -> Check:
    """
    The review gate's tests (``test_plan``): a warning under ``--allow-open`` while review.md has an open finding.
    """
    plan = ctx.test_plan
    tests = tests_pass(ctx) if plan.full else scoped_tests_pass(ctx, plan)
    if not (ctx.allow_open and ctx.review.open):
        return tests
    # A scoped plan exists only when every touched module has test_scoped configured.
    return not_blocking(ctx, tests, "review.md has open findings, which the next cycle carries", configured=None if plan.full else True)


def optional_command(key: str, name: str) -> CheckFn:
    return _named(lambda ctx: command_check(ctx, key, name, optional=True), f"{key}_passes")


CODE_COMMANDS = ("build", "typecheck", "lint")


# @req REQ-FLOW-008
def code_command(key: str, name: str) -> CheckFn:
    """
    The code gate's run of ``commands.<key>`` (blocking when it fails), or ``None`` when it is not configured.
    """
    return lambda ctx: command_check(ctx, key, name) if ctx.has_command(key) else None


# @req REQ-FLOW-008
def no_code_commands(ctx: GateContext) -> Check | None:
    """
    The code gate's warning when none of build, typecheck and lint is configured (the tests run in review), else ``None``.
    """
    if any(ctx.has_command(key) for key in CODE_COMMANDS):
        return None
    return Check("build, typecheck and lint", False, ["no build, typecheck or lint command configured: the tests run in review"], blocking=False)
