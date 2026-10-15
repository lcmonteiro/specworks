"""`specworks check`: the planning artifacts of a change are well formed (proposal, delta specs, tasks)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..core.changes import Change, list_changes
from ..core.config import ConfigError
from ..core.workspace import Workspace
from ..tools.diagrams import diagrams_in, referenced_images, state
from .capabilities import CapabilityRef, delta_files, read_spec, resolve_delta
from .specfile import (
    DELTA_SECTIONS,
    LIVING_SECTION,
    NORMATIVE_RE,
    Requirement,
    SpecDoc,
    ac_parent,
    parse_spec,
)
from .tasks import Task, parse_tasks

PROPOSAL_SECTIONS = ("Why", "What Changes", "Capabilities")
MAX_DESCRIPTION = 1000


@dataclass
class Issue:
    level: str  # "error" or "warning"
    file: str
    line: int
    message: str

    def to_dict(self) -> dict:
        return {"level": self.level, "file": self.file, "line": self.line, "message": self.message}

    def __str__(self) -> str:
        where = f"{self.file}:{self.line}" if self.line else self.file
        return f"{self.level:<7} {where}: {self.message}"


@dataclass
class Delta:
    cap: CapabilityRef
    path: Path
    doc: SpecDoc
    living: SpecDoc | None


@dataclass
class ChangeSpecs:
    """Everything parsed from a change, shared by validate and trace."""

    deltas: list[Delta] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    tasks_found: bool = False
    issues: list[Issue] = field(default_factory=list)

    def requirements(self, *sections: str) -> list[tuple[Delta, Requirement]]:
        wanted = sections or DELTA_SECTIONS
        return [(d, r) for d in self.deltas for r in d.doc.requirements if r.section in wanted]


def collect(ws: Workspace, change: Change) -> ChangeSpecs:
    result = ChangeSpecs()
    for path in delta_files(change):
        try:
            cap = resolve_delta(ws, change, path)
        except ConfigError as exc:
            result.issues.append(Issue("error", ws.rel(path), 0, str(exc)))
            continue
        doc = parse_spec(path.read_text(encoding="utf-8"))
        result.deltas.append(Delta(cap=cap, path=path, doc=doc, living=read_spec(cap.living_spec())))
    tasks_file = change.path / "tasks.md"
    if tasks_file.is_file():
        result.tasks_found = True
        result.tasks, problems = parse_tasks(tasks_file.read_text(encoding="utf-8"))
        result.issues += [Issue("error", ws.rel(tasks_file), line, msg) for line, msg in problems]
    return result


def _check_proposal(ws: Workspace, change: Change, issues: list[Issue]) -> None:
    path = change.path / "proposal.md"
    if not path.is_file():
        issues.append(Issue("error", ws.rel(path), 0, "proposal.md is missing"))
        return
    headings = {m.group(1).strip().lower() for m in re.finditer(r"^##\s+(.+)$", path.read_text(encoding="utf-8"), re.MULTILINE)}
    for section in PROPOSAL_SECTIONS:
        if section.lower() not in headings:
            issues.append(Issue("error", ws.rel(path), 0, f"missing section '## {section}'"))


def _other_changes_adding(ws: Workspace, change: Change, cap: CapabilityRef) -> dict[str, str]:
    """IDs that other active changes ADD to the same capability -> the change adding them."""
    taken = {}
    for module in ws.modules():
        for other in list_changes(module.config):
            if other.path == change.path:
                continue
            doc = read_spec(other.path / cap.delta_path)
            for req in doc.section("ADDED") if doc else []:
                if req.id:
                    taken[req.id] = module.qualify(other.name)
    return taken


def _check_delta(ws: Workspace, change: Change, delta: Delta, seen: dict[str, str], issues: list[Issue]) -> None:
    cap, doc, file = delta.cap, delta.doc, ws.rel(delta.path)

    def err(line: int, message: str) -> None:
        issues.append(Issue("error", file, line, message))

    for line, message in doc.problems:
        err(line, message)
    if not any(r.section in DELTA_SECTIONS for r in doc.requirements):
        err(0, "no requirements; add '## ADDED Requirements' (or MODIFIED / REMOVED) with '### Requirement:' blocks")
    if any(r.section == LIVING_SECTION for r in doc.requirements):
        err(0, "a delta spec uses '## ADDED/MODIFIED/REMOVED Requirements', not '## Requirements'")

    living_ids = set(delta.living.by_id()) if delta.living else set()
    if delta.living is None:
        for req in doc.requirements:
            if req.section in ("MODIFIED", "REMOVED"):
                err(req.line, f"{cap.ref} has no living spec yet, so it can only have ADDED requirements")
        if not doc.purpose:
            issues.append(Issue("warning", file, 0, f"new capability {cap.ref}: add '## Purpose' (one or two sentences)"))

    taken = _other_changes_adding(ws, change, cap)
    for req in doc.requirements:
        if req.section not in DELTA_SECTIONS:
            continue
        if req.id is None:
            err(req.line, f"requirement header must be '### Requirement: REQ-{cap.prefix}-NNN <title>'")
            continue
        if not cap.id_matches(req.id):
            err(req.line, f"{req.id}: requirements of {cap.ref} use the prefix REQ-{cap.prefix}-")
        if req.id in seen:
            err(req.line, f"{req.id} is used twice ({seen[req.id]})")
        seen[req.id] = f"{file}:{req.line}"
        if not req.title:
            err(req.line, f"{req.id} has no title")

        if req.section == "ADDED":
            if req.id in living_ids:
                err(req.line, f"{req.id} already exists in {cap.ref}; use MODIFIED to change it, or take the next free ID")
            if req.id in taken:
                err(req.line, f"{req.id} is also added by change {taken[req.id]}; take the next free ID")
        elif delta.living is not None and req.id not in living_ids:
            err(req.line, f"{req.id} is not in the living spec of {cap.ref}, so it cannot be {req.section}")

        if req.section == "REMOVED":
            if "reason" not in req.description.lower() or "migration" not in req.description.lower():
                err(req.line, f"{req.id}: a REMOVED requirement needs **Reason** and **Migration**")
            continue

        if not NORMATIVE_RE.search(req.description):
            err(req.line, f"{req.id}: state the requirement with SHALL or MUST")
        if len(req.description) > MAX_DESCRIPTION:
            issues.append(
                Issue("warning", file, req.line, f"{req.id}: description is long; keep one behaviour per requirement")
            )
        if not req.scenarios:
            err(req.line, f"{req.id} needs at least one '#### Scenario: AC-{req.id[4:]}.1 <title>' (acceptance criterion)")
        for sc in req.scenarios:
            if sc.id is None:
                err(sc.line, f"scenario header must be '#### Scenario: AC-{req.id[4:]}.<n> <title>'")
                continue
            if ac_parent(sc.id) != req.id:
                err(sc.line, f"{sc.id} is under {req.id}; number it AC-{req.id[4:]}.<n>")
            if sc.id in seen:
                err(sc.line, f"{sc.id} is used twice ({seen[sc.id]})")
            seen[sc.id] = f"{file}:{sc.line}"
            if "WHEN" not in sc.text or "THEN" not in sc.text:
                err(sc.line, f"{sc.id}: write the scenario as '- **WHEN** ...' / '- **THEN** ...'")


def _check_tasks(ws: Workspace, change: Change, specs: ChangeSpecs, issues: list[Issue]) -> None:
    file = ws.rel(change.path / "tasks.md")
    if not specs.tasks_found:
        if specs.deltas:
            issues.append(Issue("warning", file, 0, "tasks.md is not written yet"))
        return
    if not specs.tasks:
        issues.append(Issue("error", file, 0, "no tasks; use '- [ ] 1.1 description' checkboxes"))
        return

    numbers: dict[str, int] = {}
    for task in specs.tasks:
        if task.num in numbers:
            issues.append(Issue("error", file, task.line, f"task {task.num} is numbered twice (line {numbers[task.num]})"))
        numbers[task.num] = task.line

    known = set()
    for delta in specs.deltas:
        known |= {r.id for r in delta.doc.requirements if r.id} | {s.id for r in delta.doc.requirements for s in r.scenarios if s.id}
        if delta.living:
            known |= set(delta.living.by_id())
    for task in specs.tasks:
        for ref in task.ids:
            if ref not in known:
                issues.append(Issue("error", file, task.line, f"task {task.num} refers to {ref}, which is not in this change's specs"))

    mentioned = {ref for task in specs.tasks for ref in task.ids}
    for delta, req in specs.requirements("ADDED", "MODIFIED"):
        for sc in req.scenarios:
            if sc.id and sc.id not in mentioned and req.id not in mentioned:
                issues.append(
                    Issue("error", file, 0, f"{sc.id} ({delta.cap.ref}) is not covered by any task; mention {sc.id} or {req.id} in a task")
                )
    for _, req in specs.requirements("REMOVED"):
        if req.id and req.id not in mentioned:
            issues.append(Issue("warning", file, 0, f"{req.id} is REMOVED but no task removes its code and tests"))


def _check_diagrams(ws: Workspace, change: Change, issues: list[Issue]) -> None:
    settings = ws.top.config.diagrams
    design = change.path / "design.md"
    images = referenced_images(design.read_text(encoding="utf-8")) if design.is_file() else []
    for ref in images:
        if not (change.path / ref).is_file():
            issues.append(Issue("error", ws.rel(design), 0, f"image {ref} does not exist"))
    for diagram in diagrams_in(change.path):
        rel = diagram.svg.relative_to(change.path).as_posix()
        status = state(diagram, settings)
        if status != "ok":
            what = "has no SVG" if status == "missing" else "has an outdated SVG"
            issues.append(
                Issue("warning", ws.rel(diagram.source), 0, f"{what}; run `specworks diagrams --change <ref>`")
            )
        if rel not in images:
            issues.append(Issue("warning", ws.rel(diagram.source), 0, f"not shown in design.md; add ![caption]({rel})"))


def check_change(ws: Workspace, change: Change) -> tuple[ChangeSpecs, list[Issue]]:
    specs = collect(ws, change)
    issues = list(specs.issues)
    _check_proposal(ws, change, issues)

    if change.skip_specs and specs.deltas:
        issues.append(Issue("error", ws.rel(change.path), 0, "skip_specs is set but the change has delta specs"))
    if not change.skip_specs and not specs.deltas and not any(i.file.startswith(ws.rel(change.path / "specs")) for i in issues):
        issues.append(
            Issue(
                "error",
                ws.rel(change.path / "specs"),
                0,
                "no delta specs; write specs/[<module>/]<capability>/spec.md, or set skip_specs: true in "
                ".change.yaml when no behaviour changes (refactor, tooling, docs)",
            )
        )
    seen: dict[str, str] = {}
    for delta in specs.deltas:
        _check_delta(ws, change, delta, seen, issues)
    _check_tasks(ws, change, specs, issues)
    _check_diagrams(ws, change, issues)
    return specs, issues
