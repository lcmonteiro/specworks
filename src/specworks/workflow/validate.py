"""Validate phase (`specworks validate`): final, read-only check of a change before it is closed.

Every check is grouped (completeness, correctness, coherence) and names the
phase skill that fixes it. Nothing here writes to the project: it only
reads specs, tasks, tags, review.md and diagrams, and runs the project's own
test, lint and typecheck commands.
"""

from __future__ import annotations

from ..specs.capabilities import SPECS_DIR
from ..specs.check import PROPOSAL_FILE
from ..specs.tasks import TASKS_FILE
from ..tools.diagrams import diagrams_in, state
from . import checks as c
from .checks import Check, CheckFn, GateContext

COMPLETENESS, CORRECTNESS, COHERENCE = "completeness", "correctness", "coherence"
GROUPS = (COMPLETENESS, CORRECTNESS, COHERENCE)
REVIEWED_PHASES = ("review", "validate", "close")
SPECIFY, TEST, CODE, REVIEW = "/specworks-specify", "/specworks-test", "/specworks-code", "/specworks-review"


def planning_artifacts(ctx: GateContext) -> Check:
    missing = [n for n in (PROPOSAL_FILE, TASKS_FILE) if not (ctx.change.path / n).is_file()]
    if not ctx.change.skip_specs and not ctx.analysis.specs.deltas:
        missing.append(f"{SPECS_DIR}/")
    return Check("planning artifacts exist (proposal, specs, tasks)", not missing, missing)


def diagrams_current(ctx: GateContext) -> Check:
    settings = ctx.ws.top.config.diagrams
    stale = [f"{ctx.ws.rel(d.svg)} ({status})" for d in diagrams_in(ctx.change.path) if (status := state(d, settings)) != "ok"]
    return Check("diagram SVGs are up to date (specworks diagrams)", not stale, stale)


def went_through_review(ctx: GateContext) -> Check:
    in_order = ctx.change.phase in REVIEWED_PHASES
    return Check("the change went through review", in_order, [] if in_order else [f"phase is {ctx.change.phase}"], blocking=False)


# (group, the phase skill that fixes a failure, check), in report order.
VALIDATE: list[tuple[str, str, CheckFn]] = [
    # Completeness: everything the plan asked for exists and is done.
    (COMPLETENESS, SPECIFY, planning_artifacts),
    (COMPLETENESS, CODE, c.tasks_done),
    (COMPLETENESS, CODE, c.reqs_have_code),
    (COMPLETENESS, TEST, c.acs_have_tests),
    (COMPLETENESS, REVIEW, c.review_written),
    (COMPLETENESS, REVIEW, c.review_readable),
    (COMPLETENESS, REVIEW, c.review_closed),
    # Correctness: the specs are well-formed and the code does what they say.
    (CORRECTNESS, SPECIFY, c.specs_valid),
    (CORRECTNESS, SPECIFY, c.specs_warnings),
    (CORRECTNESS, SPECIFY, c.specs_as_specified),
    (CORRECTNESS, CODE, c.tests_pass),
    (CORRECTNESS, CODE, c.optional_command("lint", "lint passes (commands.lint)")),
    (CORRECTNESS, CODE, c.optional_command("typecheck", "typecheck passes (commands.typecheck)")),
    (CORRECTNESS, REVIEW, c.no_unknown_tags),
    (CORRECTNESS, CODE, c.removed_gone),
    # Coherence: code, specs, review and design tell the same story.
    (COHERENCE, REVIEW, c.files_accounted),
    (COHERENCE, REVIEW, c.diff_base),
    (COHERENCE, TEST, c.modified_tests_changed),
    (COHERENCE, SPECIFY, diagrams_current),
    (COHERENCE, REVIEW, went_through_review),
]


def validate_change(ctx: GateContext) -> list[Check]:
    checks = []
    for group, fix, check in VALIDATE:
        result = check(ctx)
        if result is not None:
            result.group, result.fix = group, fix
            checks.append(result)
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
