"""Checks shared by the phase gates and validate: the Check result and the checks several of them run."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.runner import CommandError, run_command
from ..core.workspace import Module, Workspace
from ..specs.check import ChangeSpecs
from .review import REVIEW_FILE, TYPE_PHASE, ReviewDoc, ReviewReport

# Validate groups its checks (and each failure names the phase skill that fixes it).
COMPLETENESS, CORRECTNESS, COHERENCE = "completeness", "correctness", "coherence"


@dataclass
class Check:
    name: str
    ok: bool
    details: list[str] = field(default_factory=list)
    blocking: bool = True
    group: str = ""  # validate: completeness / correctness / coherence
    fix: str = ""  # validate: the phase skill that fixes a failure

    def to_dict(self) -> dict:
        data = {"name": self.name, "ok": self.ok, "blocking": self.blocking, "details": self.details}
        if self.group:
            data["group"] = self.group
        if self.fix:
            data["fix"] = self.fix
        return data


def command_check(ws: Workspace, module: Module, key: str, name: str, run: bool, optional: bool = False, group: str = "", fix: str = "") -> Check:
    """Run ``commands.<key>``; ``optional`` commands pass (as a warning) when not configured."""
    if optional and not ws.commands(module).get(key):
        return Check(name, True, ["not configured"], blocking=False, group=group, fix=fix)
    if not run:
        return Check(name, False, [f"not run (--no-run); run `specworks run {key}`"], blocking=False, group=group, fix=fix)
    try:
        result = run_command(ws, module, key)
    except CommandError as exc:
        return Check(name, False, [str(exc)], group=group, fix=fix)
    details = [f"$ {result.command}  (in {result.cwd}, exit {result.exit_code})"]
    return Check(name, result.ok, details if result.ok else details + result.tail(), group=group, fix=fix)


def tests_pass(ws: Workspace, module: Module, run: bool) -> Check:
    return command_check(ws, module, "test", "the test suite passes (commands.test)", run, group=CORRECTNESS, fix="/specworks-code")


def spec_check(errors: list[str]) -> Check:
    return Check("specs and tasks are valid (specworks check)", not errors, errors, group=CORRECTNESS, fix="/specworks-specify")


def accounted_check(report: ReviewReport, review: ReviewDoc) -> Check:
    """Every changed file without tags is listed under "Changed files without tags" in review.md."""
    if report.changed is None:
        return Check("changed files without tags are accounted for", False, [report.note], blocking=False, group=COHERENCE, fix="/specworks-review")
    missing = [path for path in report.untraced_source + report.untraced_tests if not review.accounts_for(path)]
    return Check(f"changed files without tags are accounted for in {REVIEW_FILE} (base {report.base})", not missing, missing, group=COHERENCE, fix="/specworks-review")


def change_ids(specs: ChangeSpecs) -> set[str]:
    """Every requirement and acceptance-criterion ID in the change's delta specs."""
    return {i for d in specs.deltas for r in d.doc.requirements for i in (r.id, *(s.id for s in r.scenarios)) if i}


def tag_checks(found: dict[str, list[str]]) -> list[Check]:
    """The @req / @ac checks the code and review gates and validate share; ``found`` is ``Trace.findings()``."""
    return [
        Check("every requirement has code (@req tag)", not found["reqWithoutCode"], found["reqWithoutCode"], group=COMPLETENESS, fix="/specworks-code"),
        Check("every acceptance criterion has a test (@ac tag)", not found["acWithoutTests"], found["acWithoutTests"], group=COMPLETENESS, fix="/specworks-test"),
        Check("no tag refers to an unknown requirement or criterion", not found["unknownTags"], found["unknownTags"], group=CORRECTNESS, fix="/specworks-review"),
        Check(
            "removed requirements are gone from tests and code",
            not found["removedStillTagged"],
            found["removedStillTagged"],
            group=CORRECTNESS,
            fix="/specworks-code",
        ),
    ]


def review_checks(review: ReviewDoc, allow_open: bool = False) -> list[Check]:
    """review.md is written and has no open finding (``allow_open``: a warning, inside a build), each one routed to a phase."""
    open_findings = [f"{f.id} {f.text}" for f in review.open]
    return [
        Check(f"{REVIEW_FILE} is written", review.exists, [] if review.exists else ["write it (specworks instructions review)"], group=COMPLETENESS, fix="/specworks-review"),
        # In a build, open findings are the hand-off to the next cycle (`specworks cycle`), not a failure.
        Check(f"no open finding in {REVIEW_FILE}", review.exists and not open_findings, open_findings, blocking=not allow_open, group=COMPLETENESS, fix="/specworks-review"),
        # The next build cycle starts from each open finding's phase, so it must be known, never guessed.
        Check(
            f"every open finding has a known type ({', '.join(TYPE_PHASE)}) or a `back to <phase>:`",
            not review.unrouted,
            [f"{f.id}: type {f.type or '(none)'!r}" for f in review.unrouted],
            group=CORRECTNESS,
            fix="/specworks-review",
        ),
    ]


def reviewed_checks(ws: Workspace, module: Module, report: ReviewReport, review: ReviewDoc, run: bool, allow_open: bool = False) -> list[Check]:
    """What the review gate checks, and validate on top of its own: valid specs, review.md, tags, untagged files, tests."""
    return [
        spec_check(report.spec_errors),
        *review_checks(review, allow_open),
        *tag_checks(report.findings()),
        accounted_check(report, review),
        tests_pass(ws, module, run),
    ]
