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
from .checks import COHERENCE, COMPLETENESS, CORRECTNESS, Check, command_check, reviewed_checks
from .review import read_review, review_change

GROUPS = (COMPLETENESS, CORRECTNESS, COHERENCE)


def _check(group: str, fix: str, name: str, ok: bool, details: list[str] | None = None) -> Check:
    return Check(name, ok, details or [], group=group, fix=fix)


def validate_change(ws: Workspace, module: Module, change: Change, run: bool = True, base: str | None = None) -> list[Check]:
    report = review_change(ws, change, base)
    specs = report.trace.specs

    # Completeness: everything the plan asked for exists and is done.
    missing_artifacts = [n for n in ("proposal.md", "tasks.md") if not (change.path / n).is_file()]
    if not change.skip_specs and not specs.deltas:
        missing_artifacts.append("specs/")
    pending = [f"{t.num} {t.text}" for t in specs.tasks if not t.done]
    checks = [
        _check(COMPLETENESS, "/specworks-specify", "planning artifacts exist (proposal, specs, tasks)", not missing_artifacts, missing_artifacts),
        _check(COMPLETENESS, "/specworks-code", "every task is done", specs.tasks_found and not pending, pending),
        # Everything the review gate checks: specs valid, review.md, tags, untagged files accounted for, tests pass.
        *reviewed_checks(ws, module, report, read_review(change), run),
    ]
    for key in ("lint", "typecheck"):
        checks.append(command_check(ws, module, key, f"{key} passes (commands.{key})", run, optional=True, group=CORRECTNESS, fix="/specworks-code"))

    # Coherence: the diagrams design.md shows are rendered from their current sources.
    settings = ws.top.config.diagrams
    stale = [f"{ws.rel(d.svg)} ({status})" for d in diagrams_in(change.path) if (status := state(d, settings)) != "ok"]
    checks.append(_check(COHERENCE, "/specworks-specify", "diagram SVGs are up to date (specworks diagrams)", not stale, stale))
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
