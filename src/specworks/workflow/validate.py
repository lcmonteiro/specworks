"""
Validate phase (`specworks validate`): final check of a change before it is closed.

Every check is grouped (completeness, correctness, coherence) and names the
phase skill that fixes it. The checks write nothing to the project: they only
read specs, tasks, tags, the check artifacts and diagrams, and run the project's
own test, lint and typecheck commands. Only ``write_validation`` (`specworks
validate --write`) writes, and only validation.md.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from specworks.core.files import read_text
from specworks.specs.capabilities import SPECS_DIR
from specworks.specs.check import PROPOSAL_FILE
from specworks.specs.specfile import H2_RE, blank_comments, fenced
from specworks.specs.tasks import TASKS_FILE
from specworks.tools.diagrams import diagrams_in, state
from specworks.workflow import checks as c
from specworks.workflow.artifacts import check_artifact, check_artifacts
from specworks.workflow.checks import Check, CheckFn, GateContext
from specworks.workflow.findings import _new_artifact, add_finding, close_finding, read_findings

COMPLETENESS, CORRECTNESS, COHERENCE = "completeness", "correctness", "coherence"
GROUPS = (COMPLETENESS, CORRECTNESS, COHERENCE)
REVIEWED_PHASES = ("review", "validate", "close")
SPECIFY, DESIGN, TEST, CODE, REVIEW, CLOSE = "/specworks-specify", "/specworks-design", "/specworks-test", "/specworks-code", "/specworks-review", "/specworks-close"
VALIDATION = "validation"  # the check artifact validate writes (REQ-FLOW-019)


def planning_artifacts(ctx: GateContext) -> Check:
    missing = [n for n in (PROPOSAL_FILE, TASKS_FILE) if not (ctx.change.path / n).is_file()]
    if not ctx.change.skip_specs and not ctx.analysis.specs.deltas:
        missing.append(f"{SPECS_DIR}/")
    return Check("planning artifacts exist (proposal, specs, tasks)", not missing, missing)


# @req REQ-FLOW-013
def diagrams_current(ctx: GateContext) -> Check:
    settings = ctx.ws.top.config.diagrams
    stale = [f"{ctx.ws.rel(d.svg)} ({status})" for d in diagrams_in(ctx.change.path) if (status := state(d, settings)) != "ok"]
    return Check("diagram SVGs are up to date (specworks diagrams)", not stale, stale)


# @req REQ-FLOW-013
def architecture_diagrams_current(ctx: GateContext) -> Check | None:
    """
    A non-blocking warning naming each missing or outdated SVG in the module's ``docs/diagrams/``; None when none is.
    """
    settings = ctx.ws.top.config.diagrams
    stale = [f"{ctx.ws.rel(d.svg)} ({status})" for d in diagrams_in(ctx.module.docs_path) if (status := state(d, settings)) != "ok"]
    if not stale:
        return None
    fix = f"specworks diagrams --dir {ctx.ws.rel(ctx.module.docs_path)}"
    return Check(f"the architecture's diagram SVGs are up to date ({fix})", not stale, stale, blocking=False)


# @req REQ-FLOW-013
def went_through_review(ctx: GateContext) -> Check:
    in_order = ctx.change.phase in REVIEWED_PHASES
    return Check("the change went through review", in_order, [] if in_order else [f"phase is {ctx.change.phase}"], blocking=False)


# The check functions of each check artifact's open findings, and of validation.md's readability: write_validation
# leaves them out when it writes findings (an open finding is never a finding of its own; validation.md is what it writes).
FINDINGS_CHECKS: dict[str, CheckFn] = {}


def _findings_rows() -> list[tuple[str, str, CheckFn]]:
    rows = []
    for artifact in check_artifacts():
        if "validate" in artifact.blocks:
            readable, closed = c.artifact_readable(artifact), c.artifact_closed(artifact)
            FINDINGS_CHECKS[f"{artifact.id} closed"] = closed
            if artifact.id == VALIDATION:
                FINDINGS_CHECKS[f"{artifact.id} readable"] = readable
            rows += [(COMPLETENESS, f"/specworks-{artifact.phase}", readable), (COMPLETENESS, f"/specworks-{artifact.phase}", closed)]
    return rows


# (group, the phase skill that fixes a failure, check), in report order.
VALIDATE: list[tuple[str, str, CheckFn]] = [
    # Completeness: everything the plan asked for exists and is done.
    (COMPLETENESS, SPECIFY, planning_artifacts),
    # Open tasks by kind, each sent to the half (or design) that owns it.  @req REQ-FLOW-013
    (COMPLETENESS, TEST, c.half_tasks_done("test")),
    (COMPLETENESS, CODE, c.half_tasks_done("code")),
    (COMPLETENESS, DESIGN, c.unmarked_tasks_done),
    (COMPLETENESS, CODE, c.reqs_have_code),
    (COMPLETENESS, TEST, c.acs_have_tests),
    (COMPLETENESS, REVIEW, c.review_written),
    # Each check artifact that blocks validate is readable and has no open finding, fixed by its own step's skill.  @req REQ-FLOW-013
    *_findings_rows(),
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
    (COHERENCE, CLOSE, architecture_diagrams_current),
    (COHERENCE, REVIEW, went_through_review),
]


# @req REQ-FLOW-013, REQ-FLOW-014
def validate_change(ctx: GateContext) -> list[Check]:
    return _run(ctx, VALIDATE)


def _run(ctx: GateContext, rows: list[tuple[str, str, CheckFn]]) -> list[Check]:
    checks = []
    for group, fix, check in rows:
        result = check(ctx)
        if result is not None:
            result.group, result.fix, result.key = group, fix, check.__name__
            checks.append(result)
    return checks


# The finding type and the step of the phase skill that fixes a failed check (REQ-FLOW-019).
FIX_FINDING = {SPECIFY: ("spec-gap", "specify"), DESIGN: ("design-gap", "design"), TEST: ("test-gap", "test"), CODE: ("code-gap", "code"), REVIEW: ("quality", "review")}
CHECK_PROPOSAL = "make the check pass"
CHECK_CONFIRMED = "the check passes"
NO_FINDINGS = "None."


# @req REQ-FLOW-019
def write_validation(ctx: GateContext) -> tuple[list[Check], Path]:
    """
    Run validate and keep validation.md in step with its checks: a ``V`` finding (with its ``**Check**`` line) for each
    failed blocking check that has none open, the ones it wrote before ticked once their check passes, and the Summary
    rewritten; then the checks run again. The checks after the write, and validation.md's path.

    A finding is linked to its check by the check's key (its function's name), not by its name, which can change
    between runs (the base of the diff in "changed files without tags are accounted for ... (base <since>)").

    Every finding goes through the finding writers (each edit read back); findings without a ``**Check**`` line are
    never touched. The Summary is written from the checks after the write, so it holds the verdict validate gives.
    Implements REQ-FLOW-019, REQ-FLOW-013.
    """
    artifact = check_artifact(VALIDATION)
    path = ctx.change.path / artifact.file
    own = set(FINDINGS_CHECKS.values())
    checks = _run(ctx, [row for row in VALIDATE if row[2] not in own])
    waiting = {f.check for f in read_findings(ctx.change, artifact).open if f.check}
    failed = [check for check in checks if check.blocking and not check.ok and check.key not in waiting]
    if failed and path.is_file():
        _edit(path, lambda lines: _set_none(lines, False))  # the first finding replaces "None."
    for check in failed:
        if check.key in waiting:
            continue  # two checks of one key: one finding
        kind, step = FIX_FINDING.get(check.fix, FIX_FINDING[REVIEW])
        text = "; ".join([check.name, *check.details])
        add_finding(ctx.change, kind, text, f"back to {step}: {CHECK_PROPOSAL}", artifact=VALIDATION, check=check.key)
        waiting.add(check.key)
    passing = {check.key for check in checks if check.ok}
    for finding in read_findings(ctx.change, artifact).open:
        if finding.check in passing:
            close_finding(ctx.change, finding.id, CHECK_CONFIRMED)
    ctx.read.clear()  # the check artifacts as written
    final = validate_change(ctx)
    if not path.is_file():
        path.write_text(_new_artifact(ctx.change, artifact), encoding="utf-8")
    none = not read_findings(ctx.change, artifact).findings
    _edit(path, lambda lines: _summary(_set_none(lines, none), final))
    return final, path


def _edit(path: Path, change: Callable[[list[str]], list[str]]) -> None:
    """
    Rewrite ``path`` line by line with ``change``, keeping its line ending.
    """
    text = read_text(path, keep_newlines=True)
    newline = "\r\n" if "\r\n" in text else "\n"
    path.write_text(newline.join(change(text.splitlines())) + newline, encoding="utf-8", newline="")


def _sections(lines: list[str]) -> list[tuple[int, str]]:
    """
    Each ``##`` heading outside comments and code fences: its line and its title in lower case.
    """
    blanked = blank_comments("\n".join(lines)).split("\n")
    return [(i, h2.group("title").strip().lower()) for i, (line, example) in enumerate(zip(blanked, fenced(blanked), strict=True)) if not example and (h2 := H2_RE.match(line))]


def _section(lines: list[str], title: str) -> tuple[int, int] | None:
    """
    The heading of the section ``title`` and the line after its end (the next ``##`` heading, or the end).
    """
    headings = _sections(lines)
    for n, (at, found) in enumerate(headings):
        if found == title:
            return at, headings[n + 1][0] if n + 1 < len(headings) else len(lines)
    return None


# @req REQ-FLOW-019
def _set_none(lines: list[str], none: bool) -> list[str]:
    """
    ``lines`` with ``None.`` under ``## Findings`` when ``none``, else without it; untouched when it already is so.
    """
    found = _section(lines, "findings")
    if found is None:  # written by hand without one: before the Summary, else at the end
        if not none:
            return lines
        at = summary_at[0] if (summary_at := _section(lines, "summary")) else len(lines)
        return [*lines[:at], *([""] if at and lines[at - 1].strip() else []), "## Findings", "", NO_FINDINGS, "", *lines[at:]]
    heading, end = found
    blanked = blank_comments("\n".join(lines)).split("\n")
    marks = [i for i in range(heading + 1, end) if blanked[i].strip() == NO_FINDINGS]
    if bool(marks) == none:
        return lines
    if not none:  # with the blank line above it
        dropped = set(marks) | {i - 1 for i in marks if not lines[i - 1].strip()}
        return [line for i, line in enumerate(lines) if i not in dropped]
    last = max((i for i in range(heading + 1, end) if lines[i].strip()), default=heading)
    return [*lines[: last + 1], "", NO_FINDINGS, *([""] if last + 1 == end < len(lines) else []), *lines[last + 1 :]]


# @req REQ-FLOW-019
def _summary(lines: list[str], checks: list[Check]) -> list[str]:
    """
    ``lines`` with ``## Summary`` (to the next ``##`` heading or the end) written from ``checks``.
    """
    result = summary(checks)
    written = ["## Summary", "", f"Verdict: {result['verdict']} ({result['critical']} critical, {result['warnings']} warnings)", ""]
    written += [f"- {group.capitalize()} {counts['passed']}/{counts['total']}" for group, counts in result["groups"].items()]
    warnings = [check for check in checks if not check.blocking and not check.ok]
    if warnings:
        written += ["", "Warnings:"] + [" ".join(f"- {check.name}{': ' if check.details else ''}{'; '.join(check.details)}".split()) for check in warnings]
    found = _section(lines, "summary")
    if found is None:
        while lines and not lines[-1].strip():
            lines = lines[:-1]
        return [*lines, "", *written]
    heading, end = found
    return [*lines[:heading], *written, *([""] + lines[end:] if end < len(lines) else [])]


# @req REQ-FLOW-013
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
