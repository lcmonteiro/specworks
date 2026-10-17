"""Capabilities as seen by specs: references, ID prefixes, delta paths and living specs.

A change writes one delta spec per capability it touches, at
``specs/<module>/<capability>/spec.md`` inside the change folder, where
``<module>`` is the module's full name (``billing`` or ``billing/tax``) and is
left out for the top level (``specs/<capability>/spec.md``). The same path
means the same capability whichever module the change lives in.

The living spec of a capability is ``<capability path>/<docs_dir>/spec.md``
next to its code, with ``requirements.md`` beside it: an index whose
``## History`` records every requirement each close added, modified or
removed. A removed requirement leaves the living spec but stays in that
History, so its ID is never handed out again. A capability that is not yet in its module's config is a
*new* capability: its delta may only ADD requirements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.changes import Change, list_changes
from ..core.config import Capability, ConfigError
from ..core.files import read_text
from ..core.validators import validate_capability_name
from ..core.workspace import Module, Workspace, capability_prefix
from .specfile import REQ_ID_RE, SpecDoc, find_ids, id_prefix, parse_spec, requirement_number

SPECS_DIR = "specs"
SPEC_FILE = "spec.md"
REQUIREMENTS_FILE = "requirements.md"
HISTORY_HEADING = "## History"


@dataclass
class CapabilityRef:
    module: Module
    name: str
    capability: Capability | None  # None: new capability, not in the module's config yet

    @property
    def ref(self) -> str:
        return self.module.qualify(self.name)

    @property
    def is_new(self) -> bool:
        return self.capability is None

    @property
    def prefix(self) -> str:
        return capability_prefix(self.module.name, self.name, self.capability.prefix if self.capability else "")

    @property
    def delta_path(self) -> str:
        """Path of this capability's delta spec, relative to a change folder."""
        module = f"{self.module.name}/" if self.module.name else ""
        return f"{SPECS_DIR}/{module}{self.name}/{SPEC_FILE}"

    def living_spec(self) -> Path | None:
        if self.capability is None:
            return None
        return self.capability.docs_path(self.module.root, self.module.config.docs_dir) / SPEC_FILE

    def id_matches(self, req_id: str) -> bool:
        return REQ_ID_RE.fullmatch(req_id) is not None and id_prefix(req_id) == self.prefix


def capability_ref(module: Module, name: str) -> CapabilityRef:
    validate_capability_name(name)
    return CapabilityRef(module=module, name=name, capability=module.config.capabilities.get(name))


def resolve_ref(ws: Workspace, ref: str) -> CapabilityRef:
    """``billing:invoices`` is exact; a bare name prefers the current module, then a unique match.

    A bare name found nowhere is a new capability of the current module.
    """
    module, name = ws.split(ref)
    if module is not None:
        return capability_ref(module, name)
    if name in ws.current.config.capabilities:
        return capability_ref(ws.current, name)
    owners = [m for m in ws.modules() if name in m.config.capabilities]
    if len(owners) > 1:
        refs = ", ".join(m.qualify(name) for m in owners)
        raise ConfigError(f"capability '{name}' exists in several modules; use one of: {refs}")
    return capability_ref(owners[0] if owners else ws.current, name)


def resolve_delta(ws: Workspace, change: Change, spec_file: Path) -> CapabilityRef:
    """Capability a delta spec file belongs to, from its path under ``specs/``."""
    parts = spec_file.relative_to(change.path / SPECS_DIR).parts
    if len(parts) < 2 or parts[-1] != SPEC_FILE:
        raise ConfigError(f"delta specs must be at {SPECS_DIR}/[<module>/]<capability>/{SPEC_FILE}")
    module_name, name = "/".join(parts[:-2]), parts[-2]
    try:
        module = ws.module(module_name)
    except ConfigError:
        raise ConfigError(
            f"'{module_name}' in {SPECS_DIR}/{'/'.join(parts)} is not a module; "
            f"use {SPECS_DIR}/<capability>/{SPEC_FILE} for the top level or {SPECS_DIR}/<module>/<capability>/{SPEC_FILE}"
        ) from None
    return capability_ref(module, name)


def delta_files(change: Change) -> list[Path]:
    root = change.path / SPECS_DIR
    return sorted(root.rglob(SPEC_FILE)) if root.is_dir() else []


def read_spec(path: Path | None) -> SpecDoc | None:
    if path is None or not path.is_file():
        return None
    return parse_spec(read_text(path))


def history_lines(path: Path | None) -> list[str]:
    """The ``- ...`` lines under ``## History`` in a requirements.md (none when it does not exist)."""
    if path is None or not path.is_file():
        return []
    text = read_text(path)
    if HISTORY_HEADING not in text:
        return []
    tail = text.split(HISTORY_HEADING, 1)[1]
    return [line for line in tail.splitlines() if line.startswith("- ") and line != "- (none)"]


def history_ids(cap: CapabilityRef) -> set[str]:
    """Requirement IDs of ``cap`` that its requirements.md History says were ever added, modified or removed."""
    living = cap.living_spec()
    lines = history_lines(living.parent / REQUIREMENTS_FILE if living else None)
    return {i for line in lines for i in find_ids(line) if cap.id_matches(i)}


HISTORY_LINE_RE = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2}) `(?P<change>[^`]+)`: (?P<summary>.*)$")


def modified_since(cap: CapabilityRef, since: str) -> dict[str, str]:
    """IDs a close on or after the day of ``since`` (YYYY-MM-DD, a time may follow) MODIFIED, per requirements.md History -> ``<change> on <date>``."""
    since = since[:10]
    living = cap.living_spec()
    found: dict[str, str] = {}
    for line in history_lines(living.parent / REQUIREMENTS_FILE if living else None):
        match = HISTORY_LINE_RE.match(line)
        if not match or match.group("date") < since:
            continue
        for part in match.group("summary").split(";"):
            kind, _, ids = part.strip().partition(" ")
            if kind == "MODIFIED":
                found |= {i: f"{match.group('change')} on {match.group('date')}" for i in find_ids(ids)}
    return found


def retired_ids(cap: CapabilityRef) -> set[str]:
    """IDs that were used by ``cap`` and removed: never to be added again."""
    living = read_spec(cap.living_spec())
    return history_ids(cap) - (set(living.by_id()) if living else set())


def used_numbers(ws: Workspace, cap: CapabilityRef) -> set[int]:
    """Requirement numbers taken by the living spec, its History (removed ones too) and every active change's delta."""
    numbers: set[int] = {requirement_number(i) for i in history_ids(cap)}
    docs = [read_spec(cap.living_spec())]
    for module in ws.modules():
        for change in list_changes(module.config):
            docs.append(read_spec(change.path / cap.delta_path))
    for doc in docs:
        if doc is None:
            continue
        numbers |= {requirement_number(r.id) for r in doc.requirements if r.id and cap.id_matches(r.id)}
    return numbers


def next_id(ws: Workspace, cap: CapabilityRef) -> str:
    return f"REQ-{cap.prefix}-{max(used_numbers(ws, cap), default=0) + 1:03d}"


def describe(ws: Workspace, cap: CapabilityRef, with_scenarios: bool = True) -> dict:
    """Capability summary for agents: where its delta goes, its ID prefix and current requirements."""
    living = cap.living_spec()
    doc = read_spec(living)
    data: dict[str, Any] = {
        "ref": cap.ref,
        "module": cap.module.label,
        "name": cap.name,
        "new": cap.is_new,
        "prefix": cap.prefix,
        "nextId": next_id(ws, cap),
        "deltaPath": cap.delta_path,
        "codePath": ws.rel(cap.module.root / cap.capability.path) if cap.capability else None,
        "livingSpec": ws.rel(living) if living else None,
        "hasSpec": doc is not None,
        "purpose": doc.purpose if doc else "",
        "requirements": [],
    }
    for req in doc.requirements if doc else []:
        item: dict[str, Any] = {"id": req.id, "title": req.title}
        if with_scenarios:
            item["description"] = req.description
            item["scenarios"] = [{"id": s.id, "title": s.title, "text": s.text} for s in req.scenarios]
        data["requirements"].append(item)
    return data


def workspace_capabilities(ws: Workspace) -> list[CapabilityRef]:
    return [capability_ref(m, name) for m in ws.modules() for name in m.config.capabilities]

