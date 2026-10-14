"""Phase gates: can a change leave a phase? Each gate is a list of named checks.

A skill runs ``specworks gate <phase> --change <ref>`` before suggesting the next
phase. Gates only use facts the CLI can see (specs, tasks, @ac/@req tags); the
skills cover what needs judgement or running the project's tools (for example
that new tests fail for the right reason).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .changes import Change
from .review import REVIEW_FILE, review_change, review_findings
from .runner import CommandError, run_command
from .trace import Tag, build_matrix, gaps, scan_tags, unknown_tags
from .validate import validate_change
from .workspace import Module, Workspace

GATES = ("propose", "test", "implement", "review", "verify")


class GateError(Exception):
    """Raised for a phase without a gate."""


@dataclass
class Check:
    name: str
    ok: bool
    details: list[str] = field(default_factory=list)
    blocking: bool = True
    group: str = ""  # verify: completeness / correctness / coherence
    fix: str = ""  # verify: the phase skill that fixes a failure

    def to_dict(self) -> dict:
        data = {"name": self.name, "ok": self.ok, "blocking": self.blocking, "details": self.details}
        if self.group:
            data["group"] = self.group
        if self.fix:
            data["fix"] = self.fix
        return data


def _spec_checks(ws: Workspace, change: Change):
    specs, issues = validate_change(ws, change)
    errors = [str(i) for i in issues if i.level == "error"]
    checks = [Check("specs and tasks are valid (specworks validate)", not errors, errors)]
    return specs, checks


def _propose(ws: Workspace, change: Change) -> list[Check]:
    specs, checks = _spec_checks(ws, change)
    checks.append(
        Check(
            "tasks.md is written",
            specs.tasks_found,
            [] if specs.tasks_found else ["write tasks.md (specworks instructions tasks)"],
        )
    )
    if not change.skip_specs:
        rows = build_matrix(specs, [])
        missing = gaps(rows)["acWithoutTasks"]
        checks.append(Check("every acceptance criterion has a task", not missing, missing))
    return checks


def _test(ws: Workspace, change: Change) -> list[Check]:
    specs, checks = _spec_checks(ws, change)
    tags = scan_tags(ws)
    rows = build_matrix(specs, tags)
    found = gaps(rows)
    checks.append(
        Check(
            "every acceptance criterion has a test (@ac tag in a test file)",
            not found["acWithoutTests"],
            found["acWithoutTests"],
        )
    )
    stray = unknown_tags(specs, tags)
    checks.append(
        Check(
            "no tag refers to an unknown requirement or criterion",
            not stray,
            [f"{t.id} at {t.where}" for t in stray],
        )
    )
    misplaced = _ac_tags_outside_tests(specs_ids(specs), tags)
    checks.append(
        Check(
            "@ac tags are in test files (configure test_globs if your tests live elsewhere)",
            not misplaced,
            [f"{t.id} at {t.where}" for t in misplaced],
            blocking=False,
        )
    )
    checks.append(
        Check(
            "removed requirements are no longer tagged",
            not found["removedStillTagged"],
            found["removedStillTagged"],
            blocking=False,
        )
    )
    return checks


def _implement(ws: Workspace, module: Module, change: Change, run_tests: bool) -> list[Check]:
    specs, checks = _spec_checks(ws, change)
    pending = [f"{t.num} {t.text}" for t in specs.tasks if not t.done]
    checks.append(Check("every task is done (specworks task list --pending)", specs.tasks_found and not pending, pending))
    tags = scan_tags(ws)
    found = gaps(build_matrix(specs, tags))
    checks.append(Check("every requirement has code (@req tag)", not found["reqWithoutCode"], found["reqWithoutCode"]))
    checks.append(Check("every acceptance criterion still has a test (@ac tag)", not found["acWithoutTests"], found["acWithoutTests"]))
    stray = unknown_tags(specs, tags)
    checks.append(Check("no tag refers to an unknown requirement or criterion", not stray, [f"{t.id} at {t.where}" for t in stray]))
    checks.append(
        Check(
            "removed requirements are gone from tests and code",
            not found["removedStillTagged"],
            found["removedStillTagged"],
        )
    )
    checks.append(_tests_pass(ws, module, run_tests))
    return checks


def _review(ws: Workspace, module: Module, change: Change, run_tests: bool, base: str | None) -> list[Check]:
    specs, report = review_change(ws, change, base)
    found = report.findings()
    exists, open_findings, text = review_findings(change)
    checks = [
        Check("specs and tasks are valid (specworks validate)", not report.spec_errors, report.spec_errors),
        Check(f"{REVIEW_FILE} is written", exists, [] if exists else ["write it (specworks instructions review)"]),
        Check(f"no open finding in {REVIEW_FILE}", exists and not open_findings, open_findings),
        Check("every requirement has code (@req tag)", not found["reqWithoutCode"], found["reqWithoutCode"]),
        Check("every acceptance criterion has a test (@ac tag)", not found["acWithoutTests"], found["acWithoutTests"]),
        Check("no tag refers to an unknown requirement or criterion", not found["unknownTags"], found["unknownTags"]),
        Check("removed requirements are gone from tests and code", not found["removedStillTagged"], found["removedStillTagged"]),
    ]
    if report.changed is None:
        checks.append(Check("changed files without tags are accounted for", False, [report.note], blocking=False))
    else:
        untraced = found["untracedSource"] + found["untracedTests"]
        missing = [path for path in untraced if path not in text]
        checks.append(
            Check(
                f"changed files without tags are accounted for in {REVIEW_FILE} (base {report.base})",
                not missing,
                missing,
            )
        )
    checks.append(_tests_pass(ws, module, run_tests))
    return checks


def _tests_pass(ws: Workspace, module: Module, run_tests: bool) -> Check:
    name = "the test suite passes (commands.test)"
    if not run_tests:
        return Check(name, False, ["not run (--no-run); run `specworks run test`"], blocking=False)
    try:
        result = run_command(ws, module, "test")
    except CommandError as exc:
        return Check(name, False, [str(exc)])
    details = [f"$ {result.command}  (in {result.cwd}, exit {result.exit_code})"]
    return Check(name, result.ok, details if result.ok else details + result.tail())


def specs_ids(specs) -> set[str]:
    ids = set()
    for delta in specs.deltas:
        for req in delta.doc.requirements:
            ids |= {req.id} | {s.id for s in req.scenarios}
    return {i for i in ids if i}


def _ac_tags_outside_tests(ids: set[str], tags: list[Tag]) -> list[Tag]:
    return [t for t in tags if t.kind == "ac" and not t.is_test and t.id in ids]


def run_gate(
    ws: Workspace, module: Module, change: Change, phase: str, run_tests: bool = True, base: str | None = None
) -> tuple[bool, list[Check]]:
    if phase not in GATES:
        raise GateError(f"no gate for phase '{phase}' yet; gates exist for: {', '.join(GATES)}")
    if phase == "verify":
        from .verify import verify_change  # verify builds on the other gates' checks

        checks = verify_change(ws, module, change, run_tests, base)
    elif phase == "review":
        checks = _review(ws, module, change, run_tests, base)
    elif phase == "implement":
        checks = _implement(ws, module, change, run_tests)
    else:
        checks = {"propose": _propose, "test": _test}[phase](ws, change)
    return all(c.ok for c in checks if c.blocking), checks
