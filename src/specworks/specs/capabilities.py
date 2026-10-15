"""Capabilities as seen by specs: references, ID prefixes, delta paths and living specs.

A change writes one delta spec per capability it touches, at
``specs/<module>/<capability>/spec.md`` inside the change folder, where
``<module>`` is the module's full name (``billing`` or ``billing/tax``) and is
left out for the top level (``specs/<capability>/spec.md``). The same path
means the same capability whichever module the change lives in.

The living spec of a capability is ``<capability path>/<docs_dir>/spec.md``
next to its code. A capability that is not yet in its module's config is a
*new* capability: its delta may only ADD requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..core.changes import Change, list_changes
from ..core.config import MODULE_NAME_RE, Capability, ConfigError
from .specfile import REQ_ID_RE, SpecDoc, parse_spec, requirement_number
from ..core.workspace import Module, Workspace

SPECS_DIR = "specs"
SPEC_FILE = "spec.md"


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
        if self.capability is not None and self.capability.prefix:
            return self.capability.prefix
        parts = [*self.module.name.split("/"), self.name] if self.module.name else [self.name]
        return "-".join(parts).upper()

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
        match = REQ_ID_RE.fullmatch(req_id)
        return bool(match) and match.group("prefix") == self.prefix


def capability_ref(module: Module, name: str) -> CapabilityRef:
    if not MODULE_NAME_RE.match(name):
        raise ConfigError(f"capability name '{name}' must be kebab-case (e.g. user-auth)")
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
    return parse_spec(path.read_text(encoding="utf-8"))


def used_numbers(ws: Workspace, cap: CapabilityRef) -> set[int]:
    """Requirement numbers taken by the living spec and by every active change's delta."""
    numbers: set[int] = set()
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
    data = {
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
        item = {"id": req.id, "title": req.title}
        if with_scenarios:
            item["description"] = req.description
            item["scenarios"] = [{"id": s.id, "title": s.title, "text": s.text} for s in req.scenarios]
        data["requirements"].append(item)
    return data


def workspace_capabilities(ws: Workspace) -> list[CapabilityRef]:
    return [capability_ref(m, name) for m in ws.modules() for name in m.config.capabilities]

