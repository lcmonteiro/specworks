"""`specworks check`: the planning artifacts of a change are well formed (proposal, delta specs, tasks)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..core.changes import Change, list_changes
from ..core.config import ConfigError
from ..core.files import read_text
from ..core.workspace import Workspace
from ..tools.diagrams import diagrams_in, referenced_images, state
from .capabilities import SPECS_DIR, CapabilityRef, delta_files, modified_since, read_spec, resolve_delta, retired_ids
from .specfile import DELTA_SECTIONS, LIVING_SECTION, NORMATIVE_RE, Requirement, Scenario, SpecDoc, ac_parent, h2_titles, living_problems, parse_spec
from .tasks import TASKS_FILE, Task, parse_tasks

PROPOSAL_FILE, DESIGN_FILE = "proposal.md", "design.md"
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

    def dropped_criteria(self, req: Requirement) -> list[Scenario]:
        """Living criteria that go with ``req`` at close: those a MODIFIED block leaves out, every one of a REMOVED requirement."""
        if req.section not in ("MODIFIED", "REMOVED") or self.living is None:
            return []
        old = self.living.by_id().get(req.id or "")
        kept = {sc.id for sc in req.scenarios} if req.section == "MODIFIED" else set()
        return [sc for sc in old.scenarios if sc.id and sc.id not in kept] if old else []


@dataclass
class ChangeSpecs:
    """Everything parsed from a change, shared by validate and trace."""

    deltas: list[Delta] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    tasks_found: bool = False
    issues: list[Issue] = field(default_factory=list)

    def known_ids(self) -> set[str]:
        """Every ID in the deltas and in the living specs they change."""
        return {i for d in self.deltas for doc in (d.doc, d.living) if doc for i in doc.ids()}

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
        doc = parse_spec(read_text(path))
        result.deltas.append(Delta(cap=cap, path=path, doc=doc, living=read_spec(cap.living_spec())))
    tasks_file = change.path / TASKS_FILE
    if tasks_file.is_file():
        result.tasks_found = True
        result.tasks, problems = parse_tasks(read_text(tasks_file))
        result.issues += [Issue("error", ws.rel(tasks_file), line, msg) for line, msg in problems]
    return result


def _check_proposal(ws: Workspace, change: Change, issues: list[Issue]) -> None:
    path = change.path / PROPOSAL_FILE
    if not path.is_file():
        issues.append(Issue("error", ws.rel(path), 0, f"{PROPOSAL_FILE} is missing"))
        return
    headings = {title.strip().lower() for title in h2_titles(read_text(path))}
    for section in PROPOSAL_SECTIONS:
        if section.lower() not in headings:
            issues.append(Issue("error", ws.rel(path), 0, f"missing section '## {section}'"))


def _active_others(ws: Workspace, change: Change) -> list[tuple[str, Change]]:
    return [(module.qualify(other.name), other) for module in ws.modules() for other in list_changes(module.config) if other.path != change.path]


@dataclass
class Claim:
    """An ID that another active change also puts in a delta section."""

    change: str
    earlier: bool  # that change started before this one


def _other_changes(ws: Workspace, change: Change, cap: CapabilityRef) -> dict[str, dict[str, Claim]]:
    """For each delta section, the IDs that other active changes put there for the same capability -> their claim."""
    claimed: dict[str, dict[str, Claim]] = {section: {} for section in DELTA_SECTIONS}
    for name, other in _active_others(ws, change):
        doc = read_spec(other.path / cap.delta_path)
        for req in doc.requirements if doc else []:
            if req.id and req.section in claimed:
                claimed[req.section][req.id] = Claim(name, other.order < change.order)
    return claimed


def other_deltas(ws: Workspace, change: Change) -> list[tuple[CapabilityRef, SpecDoc]]:
    """The delta specs of every other active change (those whose capability cannot be resolved are left out)."""
    found = []
    for _, other in _active_others(ws, change):
        for path in delta_files(other):
            try:
                found.append((resolve_delta(ws, other, path), parse_spec(read_text(path))))
            except ConfigError:
                continue
    return found


REMOVAL_FIELDS = ("Reason", "Migration")


def _removal_fields(description: str) -> set[str]:
    """Labels of the ``Reason: ...`` / ``**Migration**: ...`` lines (bold and a bullet allowed) that have text after them."""
    found = set()
    for line in description.splitlines():
        label, colon, text = line.replace("*", "").strip().removeprefix("- ").partition(":")
        if colon and text.strip() and label.strip().lower() in ("reason", "migration"):
            found.add(label.strip().lower())
    return found


def _check_delta(ws: Workspace, change: Change, delta: Delta, seen: dict[str, str], issues: list[Issue]) -> None:
    cap, doc, file = delta.cap, delta.doc, ws.rel(delta.path)

    def err(line: int, message: str) -> None:
        issues.append(Issue("error", file, line, message))

    def warn(line: int, message: str) -> None:
        issues.append(Issue("warning", file, line, message))

    for line, message in doc.problems:
        err(line, message)
    if not any(r.section in DELTA_SECTIONS for r in doc.requirements):
        err(0, "no requirements; add '## ADDED Requirements' (or MODIFIED / REMOVED) with '### Requirement:' blocks")
    if any(r.section == LIVING_SECTION for r in doc.requirements):
        err(0, "a delta spec uses '## ADDED/MODIFIED/REMOVED Requirements', not '## Requirements'")

    if delta.living is not None and (living_path := cap.living_spec()) is not None:
        for line, message in living_problems(delta.living):
            issues.append(Issue("warning", ws.rel(living_path), line, f"living spec of {cap.ref}: {message}; fix it before closing"))

    living_ids = set(delta.living.by_id()) if delta.living else set()
    if delta.living is None:
        for req in doc.requirements:
            if req.section in ("MODIFIED", "REMOVED"):
                err(req.line, f"{cap.ref} has no living spec yet, so it can only have ADDED requirements")
        if not doc.purpose:
            issues.append(Issue("warning", file, 0, f"new capability {cap.ref}: add '## Purpose' (one or two sentences)"))

    if cap.is_new and (owner := ws.prefixes().get(cap.prefix)):
        err(
            0,
            f"new capability {cap.ref} would use the ID prefix {cap.prefix}, already used by {owner}; "
            f"register it with its own prefix first (specworks capability add {cap.name} --path <code path> --prefix <PREFIX>)",
        )

    others = _other_changes(ws, change, cap)
    taken = others["ADDED"]
    # Each MODIFIED/REMOVED block replaces the whole living block at close, so two changes
    # editing one requirement would lose the first one's edit: one has to close first.
    # Only the change that started later gets the error, so two changes never block each other.
    edited = {**others["REMOVED"], **others["MODIFIED"]}
    retired = retired_ids(cap)
    # A change that closed after this one started may have edited a block this one copied before.
    closed_since = modified_since(cap, change.created) if change.created else {}
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
            if req.id in retired:
                err(req.line, f"{req.id} was removed from {cap.ref} (requirements.md History); IDs are never reused, take the next free ID")
            if claim := taken.get(req.id):
                if claim.earlier:
                    err(req.line, f"{req.id} is also added by change {claim.change}, which started first; take the next free ID")
                else:
                    warn(req.line, f"{req.id} is also added by change {claim.change}, which started later and has to take another ID")
        elif delta.living is not None and req.id not in living_ids:
            err(req.line, f"{req.id} is not in the living spec of {cap.ref}, so it cannot be {req.section}")
        elif claim := edited.get(req.id):
            if claim.earlier:
                err(
                    req.line,
                    f"{req.id} is also MODIFIED or REMOVED by change {claim.change}, which started first; close it first, "
                    "then copy the requirement again from the living spec here",
                )
            else:
                warn(
                    req.line,
                    f"{req.id} is also MODIFIED or REMOVED by change {claim.change}, which started later; "
                    "it waits until this change closes",
                )
        if req.section == "MODIFIED" and req.id in closed_since:
            warn(req.line, f"{req.id} was MODIFIED by {closed_since[req.id]}, after this change started; "
                           "make sure this block is copied from the current living spec, or closing undoes those edits")
        if req.section == "MODIFIED" and (dropped := [str(sc.id) for sc in delta.dropped_criteria(req)]):
            warn(req.line, f"{req.id}: this MODIFIED block drops {', '.join(dropped)}; copy the whole block "
                           "from the living spec, or drop a criterion only on purpose (with its tests)")

        if req.section == "REMOVED":
            if missing := [f for f in REMOVAL_FIELDS if f.lower() not in _removal_fields(req.description)]:
                err(req.line, f"{req.id}: a REMOVED requirement needs **Reason** and **Migration** lines, each with its text "
                              f"(missing: {', '.join(missing)}); e.g. '**Reason**: replaced by SSO'")
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
    file = ws.rel(change.path / TASKS_FILE)
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

    known = specs.known_ids()
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
    design = change.path / DESIGN_FILE
    images = referenced_images(read_text(design)) if design.is_file() else []
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
    specs_dir = ws.rel(change.path / SPECS_DIR)
    if not change.skip_specs and not specs.deltas and not any(i.file.startswith(specs_dir) for i in issues):
        issues.append(
            Issue(
                "error",
                specs_dir,
                0,
                "no delta specs; write specs/[<module>/]<capability>/spec.md, or run "
                "`specworks skip-specs --change <ref>` when no behaviour changes (refactor, tooling, docs)",
            )
        )
    seen: dict[str, str] = {}
    for delta in specs.deltas:
        _check_delta(ws, change, delta, seen, issues)
    _check_tasks(ws, change, specs, issues)
    _check_diagrams(ws, change, issues)
    return specs, issues
