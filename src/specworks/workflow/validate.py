"""Validate phase (`specworks validate`): final, read-only check of a change before it is closed.

Every check is grouped (completeness, correctness, coherence) and names the
phase skill that fixes it. Nothing here writes to the project: it only
reads specs, tasks, tags, review.md and diagrams, and runs the project's own
test, lint and typecheck commands.
"""

from __future__ import annotations

from ..core.changes import Change
from ..core.workspace import Module, Workspace
from ..tools.diagrams import diagrams_in, state
from .checks import COHERENCE, COMPLETENESS, CORRECTNESS, Check, accounted_check, command_check, tag_checks, tests_pass
from .review import REVIEW_FILE, read_review, review_change

GROUPS = (COMPLETENESS, CORRECTNESS, COHERENCE)
REVIEWED_PHASES = ("review", "validate", "close")


def _check(group: str, fix: str, name: str, ok: bool, details: list[str] | None = None, blocking: bool = True) -> Check:
    return Check(name, ok, details or [], blocking=blocking, group=group, fix=fix)


def _grouped(check: Check, group: str, fix: str) -> Check:
    check.group, check.fix = group, fix
    return check


def validate_change(ws: Workspace, module: Module, change: Change, run: bool = True, base: str | None = None) -> list[Check]:
    specs, report = review_change(ws, change, base)
    found = report.findings()
    review = read_review(change)
    reviewed, open_findings = review.exists, [f"{f.id} {f.text}" for f in review.open]
    checks: list[Check] = []

    # Completeness: everything the plan asked for exists and is done.
    missing_artifacts = [n for n in ("proposal.md", "tasks.md") if not (change.path / n).is_file()]
    if not change.skip_specs and not specs.deltas:
        missing_artifacts.append("specs/")
    checks.append(_check(COMPLETENESS, "/specworks-specify", "planning artifacts exist (proposal, specs, tasks)", not missing_artifacts, missing_artifacts))
    pending = [f"{t.num} {t.text}" for t in specs.tasks if not t.done]
    checks.append(_check(COMPLETENESS, "/specworks-code", "every task is done", specs.tasks_found and not pending, pending))
    review_details = [] if reviewed else [f"{REVIEW_FILE} is missing"]
    checks.append(
        _check(COMPLETENESS, "/specworks-review", f"review done ({REVIEW_FILE} with no open finding)", reviewed and not open_findings, review_details + open_findings)
    )

    # Correctness: the specs are well-formed and the code does what they say.
    checks.append(_check(CORRECTNESS, "/specworks-specify", "specs and tasks are valid (specworks check)", not report.spec_errors, report.spec_errors))
    checks.append(_grouped(tests_pass(ws, module, run), CORRECTNESS, "/specworks-code"))
    for key in ("lint", "typecheck"):
        command = command_check(ws, module, key, f"{key} passes (commands.{key})", run, optional=True)
        checks.append(_grouped(command, CORRECTNESS, "/specworks-code"))
    checks += tag_checks(found)  # @req code and @ac tests (completeness), unknown and removed tags (correctness)

    # Coherence: code, specs, review and design tell the same story.
    checks.append(_grouped(accounted_check(report, review), COHERENCE, "/specworks-review"))
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
