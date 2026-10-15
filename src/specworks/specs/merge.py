"""Merge a change's delta specs into the living specs and archive the change.

The living spec of a capability (``<code path>/<docs_dir>/spec.md``) is edited
as text so everything outside the requirement blocks is kept as written:

- ADDED blocks are appended at the end of ``## Requirements``;
- MODIFIED blocks replace the block with the same ID, in place;
- REMOVED blocks are deleted.

``requirements.md`` next to it is regenerated: an index of the current
requirements and criteria, plus a ``## History`` section that each close
appends to. Every file is computed first; nothing is written if any delta
cannot be applied.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from ..core.changes import Change
from ..core.workspace import Workspace
from .capabilities import CapabilityRef
from .check import ChangeSpecs, Delta
from .specfile import LIVING_SECTION, Requirement, parse_spec, section_kind

REQUIREMENTS_FILE = "requirements.md"
HISTORY_HEADING = "## History"


class MergeError(Exception):
    """Raised when a delta cannot be applied to its living spec."""


@dataclass
class CapabilityMerge:
    cap: CapabilityRef
    spec_path: Path
    created: bool
    added: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    spec_text: str = ""
    requirements_text: str = ""

    @property
    def requirements_path(self) -> Path:
        return self.spec_path.parent / REQUIREMENTS_FILE

    def summary(self) -> str:
        parts = [f"{kind} {', '.join(ids)}" for kind, ids in (("ADDED", self.added), ("MODIFIED", self.modified), ("REMOVED", self.removed)) if ids]
        return "; ".join(parts)

    def to_dict(self, ws: Workspace) -> dict:
        return {
            "capability": self.cap.ref,
            "spec": ws.rel(self.spec_path),
            "requirements": ws.rel(self.requirements_path),
            "created": self.created,
            "added": self.added,
            "modified": self.modified,
            "removed": self.removed,
        }


def _blocks(lines: list[str]) -> tuple[int, int, list[tuple[str | None, int, int]]]:
    """Locate '## Requirements' and its requirement blocks as 0-based line indexes: (section start, section end, [(id, start, end)]).

    The blocks come from ``parse_spec``, so headings inside code fences are not mistaken for structure.
    """
    doc = parse_spec("\n".join(lines))
    starts = [number for number, title in doc.sections if section_kind(title) == LIVING_SECTION]
    if not starts:
        raise MergeError("the living spec has no '## Requirements' section")
    start = starts[0]
    end = next((number for number, _ in doc.sections if number > start), len(lines) + 1)
    blocks = [(r.id, r.line - 1, r.end) for r in doc.requirements if start < r.line < end]
    return start - 1, end - 1, blocks


def _block_lines(req: Requirement) -> list[str]:
    return req.markdown().rstrip("\n").split("\n") + [""]


def new_spec_text(cap: CapabilityRef, purpose: str) -> str:
    purpose = purpose.strip() or f"TBD: describe what {cap.ref} is for."
    return f"# {cap.ref}\n\n## Purpose\n\n{purpose}\n\n## Requirements\n"


def apply_delta(living_text: str, delta: Delta) -> tuple[str, list[str], list[str], list[str]]:
    """New living spec text plus the IDs added, modified and removed."""
    lines = living_text.rstrip("\n").split("\n")
    _, section_end, blocks = _blocks(lines)
    by_id = {req_id: (start, end) for req_id, start, end in blocks if req_id}
    added, modified, removed = [], [], []
    replacements: dict[int, tuple[int, list[str]]] = {}

    for req in delta.doc.requirements:
        if req.section == "MODIFIED":
            if req.id not in by_id:
                raise MergeError(f"{req.id} is MODIFIED but not in the living spec of {delta.cap.ref}")
            start, end = by_id[req.id]
            replacements[start] = (end, _block_lines(req))
            modified.append(req.id)
        elif req.section == "REMOVED":
            if req.id not in by_id:
                raise MergeError(f"{req.id} is REMOVED but not in the living spec of {delta.cap.ref}")
            start, end = by_id[req.id]
            replacements[start] = (end, [])
            removed.append(req.id)
        elif req.section == "ADDED" and req.id in by_id:
            raise MergeError(f"{req.id} is ADDED but already in the living spec of {delta.cap.ref}")

    out: list[str] = []
    i = 0
    while i <= len(lines):
        if i == section_end:  # ADDED blocks go at the end of '## Requirements'
            if out and out[-1].strip():
                out.append("")
            for req in delta.doc.section("ADDED"):
                out += _block_lines(req)
                added.append(req.id or "?")  # check_change requires IDs before close
        if i == len(lines):
            break
        if i in replacements:
            end, new_lines = replacements[i]
            out += new_lines
            i = end
            continue
        out.append(lines[i])
        i += 1
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).rstrip("\n") + "\n"
    return text, added, modified, removed


def requirements_index(cap: CapabilityRef, spec_text: str, history: list[str]) -> str:
    doc = parse_spec(spec_text)
    out = [
        f"# Requirements: {cap.ref}",
        "",
        "Generated by `specworks close` from spec.md; do not edit by hand.",
        "",
        "| Requirement | Title | Acceptance criteria |",
        "|---|---|---|",
    ]
    for req in doc.section(LIVING_SECTION):
        acs = ", ".join(s.id for s in req.scenarios if s.id) or "—"
        out.append(f"| {req.id} | {req.title} | {acs} |")
    out += ["", HISTORY_HEADING, ""] + (history or ["- (none)"])
    return "\n".join(out) + "\n"


def _history(path: Path) -> list[str]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    if HISTORY_HEADING not in text:
        return []
    tail = text.split(HISTORY_HEADING, 1)[1]
    return [line for line in tail.splitlines() if line.startswith("- ") and line != "- (none)"]


def plan_merge(ws: Workspace, change: Change, specs: ChangeSpecs, change_ref: str, today: str | None = None) -> list[CapabilityMerge]:
    """Compute every living spec and requirements index this change produces, without writing."""
    today = today or date.today().isoformat()
    unregistered = [d.cap.ref for d in specs.deltas if d.cap.capability is None]
    if unregistered:
        raise MergeError(
            "new capabilities must be registered before closing: "
            + ", ".join(unregistered)
            + " (specworks capability add <name> --path <code path> [--module <module>])"
        )
    merges = []
    for delta in specs.deltas:
        spec_path = delta.cap.living_spec()
        assert spec_path is not None  # every capability is registered (checked above)
        created = not spec_path.is_file()
        living = spec_path.read_text(encoding="utf-8") if not created else new_spec_text(delta.cap, delta.doc.purpose)
        try:
            text, added, modified, removed = apply_delta(living, delta)
        except MergeError as exc:
            raise MergeError(f"{ws.rel(spec_path)}: {exc}") from None
        merge = CapabilityMerge(delta.cap, spec_path, created, added, modified, removed, text)
        history = _history(merge.requirements_path) + [f"- {today} `{change_ref}`: {merge.summary() or 'no requirement changes'}"]
        merge.requirements_text = requirements_index(delta.cap, text, history)
        merges.append(merge)
    return merges


def write_merge(merges: list[CapabilityMerge]) -> None:
    for merge in merges:
        merge.spec_path.parent.mkdir(parents=True, exist_ok=True)
        merge.spec_path.write_text(merge.spec_text, encoding="utf-8")
        merge.requirements_path.write_text(merge.requirements_text, encoding="utf-8")


def archive_target(change: Change, archive_root: Path, today: str | None = None) -> Path:
    """Where the change is archived (<archive>/<date>-<name>/); fails if that folder is taken."""
    target = archive_root / f"{today or date.today().isoformat()}-{change.name}"
    if target.exists():
        raise MergeError(f"{target} already exists")
    return target


def archive_change(change: Change, archive_root: Path, today: str | None = None) -> Path:
    """Mark the change done and move it to <archive>/<date>-<name>/."""
    target = archive_target(change, archive_root, today)
    phase = change.phase
    change.phase = "done"
    change.save()
    try:
        archive_root.mkdir(parents=True, exist_ok=True)
        shutil.move(str(change.path), str(target))
    except OSError:
        change.phase = phase
        change.save()
        raise
    return target


def close_change(merges: list[CapabilityMerge], change: Change, archive_root: Path, today: str | None = None) -> Path:
    """Write the merged living docs and archive the change, all or nothing.

    The archive folder is checked before anything is written; if writing or
    archiving fails, every living file is put back as it was.
    """
    today = today or date.today().isoformat()
    archive_target(change, archive_root, today)
    paths = [p for m in merges for p in (m.spec_path, m.requirements_path)]
    originals = {p: p.read_text(encoding="utf-8") if p.is_file() else None for p in paths}
    try:
        write_merge(merges)
        return archive_change(change, archive_root, today)
    except BaseException:
        for path, text in originals.items():
            if text is not None:
                path.write_text(text, encoding="utf-8")
            elif path.is_file():
                path.unlink()
        raise
