"""Phase gates: can a change leave a phase? Each gate is a list of named checks.

A skill runs ``specworks gate <phase> --change <ref>`` before suggesting the next
phase. Gates only use facts the CLI can see (specs, tasks, @ac/@req tags); the
skills cover what needs judgement or running the project's tools (for example
that new tests fail for the right reason).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .changes import Change
from .trace import Tag, build_matrix, gaps, scan_tags, unknown_tags
from .validate import validate_change
from .workspace import Workspace

GATES = ("propose", "test")


class GateError(Exception):
    """Raised for a phase without a gate."""


@dataclass
class Check:
    name: str
    ok: bool
    details: list[str] = field(default_factory=list)
    blocking: bool = True

    def to_dict(self) -> dict:
        return {"name": self.name, "ok": self.ok, "blocking": self.blocking, "details": self.details}


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


def specs_ids(specs) -> set[str]:
    ids = set()
    for delta in specs.deltas:
        for req in delta.doc.requirements:
            ids |= {req.id} | {s.id for s in req.scenarios}
    return {i for i in ids if i}


def _ac_tags_outside_tests(ids: set[str], tags: list[Tag]) -> list[Tag]:
    return [t for t in tags if t.kind == "ac" and not t.is_test and t.id in ids]


def run_gate(ws: Workspace, change: Change, phase: str) -> tuple[bool, list[Check]]:
    if phase not in GATES:
        raise GateError(f"no gate for phase '{phase}' yet; gates exist for: {', '.join(GATES)}")
    checks = {"propose": _propose, "test": _test}[phase](ws, change)
    return all(c.ok for c in checks if c.blocking), checks
