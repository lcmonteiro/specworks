"""Validate phase (`specworks validate`): final, read-only check of a change before it is closed.

Every check is grouped (completeness, correctness, coherence) and names the
phase skill that fixes it. Nothing here writes to the project: it only
reads specs, tasks, tags, review.md and diagrams, and runs the project's own
test, lint and typecheck commands.
"""

from __future__ import annotations

from ..core.changes import Change
from ..tools.diagrams import diagrams_in, state
from .gate import Check, _tests_pass
from .review import REVIEW_FILE, review_change, review_findings
from ..core.runner import CommandError, run_command
from ..core.workspace import Module, Workspace

COMPLETENESS, CORRECTNESS, COHERENCE = "completeness", "correctness", "coherence"
GROUPS = (COMPLETENESS, CORRECTNESS, COHERENCE)
REVIEWED_PHASES = ("review", "validate", "close")


def _check(group: str, fix: str, name: str, ok: bool, details: list[str] | None = None, blocking: bool = True) -> Check:
    return Check(name, ok, details or [], blocking=blocking, group=group, fix=fix)


def _optional_command(ws: Workspace, module: Module, key: str, run: bool) -> Check:
    name = f"{key} passes (commands.{key})"
    if not ws.commands(module).get(key):
        return _check(CORRECTNESS, "/specworks-code", name, True, ["not configured"], blocking=False)
    if not run:
        return _check(CORRECTNESS, "/specworks-code", name, False, ["not run (--no-run)"], blocking=False)
    try:
        result = run_command(ws, module, key)
    except CommandError as exc:
        return _check(CORRECTNESS, "/specworks-code", name, False, [str(exc)])
    details = [f"$ {result.command}  (in {result.cwd}, exit {result.exit_code})"]
    return _check(CORRECTNESS, "/specworks-code", name, result.ok, details if result.ok else details + result.tail())


def validate_change(ws: Workspace, module: Module, change: Change, run: bool = True, base: str | None = None) -> list[Check]:
    specs, report = review_change(ws, change, base)
    found = report.findings()
    reviewed, open_findings, review_text = review_findings(change)
    checks: list[Check] = []

    # Completeness: everything the plan asked for exists and is done.
    missing_artifacts = [n for n in ("proposal.md", "tasks.md") if not (change.path / n).is_file()]
    if not change.skip_specs and not specs.deltas:
        missing_artifacts.append("specs/")
    checks.append(_check(COMPLETENESS, "/specworks-specify", "planning artifacts exist (proposal, specs, tasks)", not missing_artifacts, missing_artifacts))
    pending = [f"{t.num} {t.text}" for t in specs.tasks if not t.done]
    checks.append(_check(COMPLETENESS, "/specworks-code", "every task is done", specs.tasks_found and not pending, pending))
    checks.append(_check(COMPLETENESS, "/specworks-code", "every requirement has code (@req)", not found["reqWithoutCode"], found["reqWithoutCode"]))
    checks.append(_check(COMPLETENESS, "/specworks-test", "every acceptance criterion has a test (@ac)", not found["acWithoutTests"], found["acWithoutTests"]))
    review_details = [] if reviewed else [f"{REVIEW_FILE} is missing"]
    checks.append(
        _check(COMPLETENESS, "/specworks-review", f"review done ({REVIEW_FILE} with no open finding)", reviewed and not open_findings, review_details + open_findings)
    )

    # Correctness: the specs are well-formed and the code does what they say.
    checks.append(_check(CORRECTNESS, "/specworks-specify", "specs and tasks are valid (specworks check)", not report.spec_errors, report.spec_errors))
    test_check = _tests_pass(ws, module, run)
    test_check.group, test_check.fix = CORRECTNESS, "/specworks-code"
    checks.append(test_check)
    checks.append(_optional_command(ws, module, "lint", run))
    checks.append(_optional_command(ws, module, "typecheck", run))
    checks.append(_check(CORRECTNESS, "/specworks-review", "no tag refers to an unknown requirement or criterion", not found["unknownTags"], found["unknownTags"]))
    checks.append(_check(CORRECTNESS, "/specworks-code", "removed requirements are gone from tests and code", not found["removedStillTagged"], found["removedStillTagged"]))

    # Coherence: code, specs, review and design tell the same story.
    if report.changed is None:
        checks.append(_check(COHERENCE, "/specworks-review", "changed files without tags are accounted for", False, [report.note], blocking=False))
    else:
        untraced = found["untracedSource"] + found["untracedTests"]
        missing = [path for path in untraced if path not in review_text]
        checks.append(
            _check(COHERENCE, "/specworks-review", f"changed files without tags are accounted for in {REVIEW_FILE} (base {report.base})", not missing, missing)
        )
    settings = ws.top.config.diagrams
    stale = [f"{ws.rel(d.svg)} ({status})" for d in diagrams_in(change.path) if (status := state(d, settings)) != "ok"]
    checks.append(_check(COHERENCE, "/specworks-specify", "diagram SVGs are up to date (specworks diagrams)", not stale, stale))
    in_order = change.phase in REVIEWED_PHASES
    checks.append(
        _check(COHERENCE, "/specworks-review", "the change went through review", in_order, [] if in_order else [f"phase is {change.phase}"], blocking=False)
    )
    return checks


def summary(checks: list[Check]) -> dict:
    critical = [c for c in checks if c.blocking and not c.ok]
    warnings = [c for c in checks if not c.blocking and not c.ok]
    return {
        "verdict": "PASS" if not critical else "FAIL",
        "critical": len(critical),
        "warnings": len(warnings),
        "groups": {g: {"passed": sum(c.ok for c in checks if c.group == g), "total": sum(c.group == g for c in checks)} for g in GROUPS},
        "goBackTo": sorted({c.fix for c in critical}),
    }
