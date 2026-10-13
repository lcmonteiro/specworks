"""Artifact graph of a change: what exists, what is ready, and how to write each artifact."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache
from importlib import resources

import yaml

from .changes import Change
from .workspace import Module, Workspace


@dataclass
class Artifact:
    id: str
    phase: str
    generates: str
    template: str
    instruction: str
    requires: list[str] = field(default_factory=list)
    optional: bool = False

    def exists(self, change: Change) -> bool:
        if any(ch in self.generates for ch in "*?["):
            return any(p.is_file() for p in change.path.glob(self.generates))
        return (change.path / self.generates).is_file()


class WorkflowError(Exception):
    """Raised for unknown artifacts."""


@cache
def load_artifacts() -> dict[str, Artifact]:
    text = resources.files("specworks").joinpath("schema.yaml").read_text(encoding="utf-8")
    raw = yaml.safe_load(text)
    return {item["id"]: Artifact(**item) for item in raw["artifacts"]}


def read_template(name: str) -> str:
    return resources.files("specworks").joinpath("templates", name).read_text(encoding="utf-8")


def artifact_states(change: Change) -> list[dict]:
    """Each artifact as done, ready (all requirements exist) or blocked."""
    artifacts = load_artifacts()
    states = []
    for art in artifacts.values():
        if art.exists(change):
            status = "done"
        else:
            missing = [r for r in art.requires if not artifacts[r].exists(change) and not artifacts[r].optional]
            status = "blocked" if missing else "ready"
        states.append(
            {
                "id": art.id,
                "phase": art.phase,
                "generates": art.generates,
                "status": status,
                "requires": art.requires,
                "optional": art.optional,
            }
        )
    return states


def instructions(ws: Workspace, module: Module, change: Change, artifact_id: str) -> dict:
    artifacts = load_artifacts()
    if artifact_id not in artifacts:
        raise WorkflowError(f"unknown artifact '{artifact_id}'; expected one of {', '.join(artifacts)}")
    art = artifacts[artifact_id]
    return {
        "artifact": art.id,
        "phase": art.phase,
        "change": module.qualify(change.name),
        "module": module.label,
        "root": str(ws.root),
        "changeDir": ws.rel(change.path),
        "outputPath": f"{ws.rel(change.path)}/{art.generates}",
        "exists": art.exists(change),
        "optional": art.optional,
        "context": ws.merged_context(module),
        "instruction": art.instruction,
        "template": read_template(art.template),
        "dependencies": [
            {
                "id": dep,
                "path": f"{ws.rel(change.path)}/{artifacts[dep].generates}",
                "done": artifacts[dep].exists(change),
            }
            for dep in art.requires
        ],
    }
