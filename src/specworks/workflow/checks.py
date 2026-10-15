"""Checks shared by the phase gates and validate: the Check result and the checks both run."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.runner import CommandError, cached_run
from ..core.workspace import Module, Workspace
from ..specs.check import ChangeSpecs
from .review import REVIEW_FILE, ReviewDoc, ReviewReport


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


def command_check(ws: Workspace, module: Module, key: str, name: str, run: bool, optional: bool = False) -> Check:
    """Run ``commands.<key>``; ``optional`` commands pass (as a warning) when not configured."""
    if optional and not ws.commands(module).get(key):
        return Check(name, True, ["not configured"], blocking=False)
    if not run:
        return Check(name, False, [f"not run (--no-run); run `specworks run {key}`"], blocking=False)
    try:
        result = cached_run(ws, module, key)
    except CommandError as exc:
        return Check(name, False, [str(exc)])
    reused = f", same code as the run at {result.cached_at}" if result.cached_at else ""
    details = [f"$ {result.command}  (in {result.cwd}, exit {result.exit_code}{reused})"]
    return Check(name, result.ok, details if result.ok else details + result.tail())


def tests_pass(ws: Workspace, module: Module, run: bool) -> Check:
    return command_check(ws, module, "test", "the test suite passes (commands.test)", run)


def accounted_check(report: ReviewReport, review: ReviewDoc) -> Check:
    """Every changed file without tags is listed under "Changed files without tags" in review.md."""
    if report.changed is None:
        return Check("changed files without tags are accounted for", False, [report.note], blocking=False)
    missing = [path for path in report.untraced_source + report.untraced_tests if not review.accounts_for(path)]
    return Check(f"changed files without tags are accounted for in {REVIEW_FILE} (base {report.base})", not missing, missing)


def change_ids(specs: ChangeSpecs) -> set[str]:
    """Every requirement and acceptance-criterion ID in the change's delta specs."""
    return {i for d in specs.deltas for r in d.doc.requirements for i in (r.id, *(s.id for s in r.scenarios)) if i}
