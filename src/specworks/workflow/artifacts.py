"""Artifact graph of a change: what exists, what is ready, and how to write each artifact."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cache
from importlib import resources

import yaml

from specworks.core.changes import HALVES, Change
from specworks.core.config import ConfigError
from specworks.core.errors import SpecworksError
from specworks.core.files import read_text
from specworks.core.workspace import Module, Workspace
from specworks.specs.capabilities import delta_files, describe, resolve_delta, workspace_capabilities
from specworks.specs.tasks import TASKS_FILE, parse_tasks


@dataclass
class Artifact:
    id: str
    phase: str
    generates: str
    instruction: str
    template: str = ""
    requires: list[str] = field(default_factory=list)
    optional: bool = False
    findings: dict | None = None  # a check artifact's ``{letter, blocks}`` (REQ-FLOW-018); None for the others

    def skipped(self, change: Change) -> bool:
        """Delta specs of a change with no behaviour change (``skip_specs``) are not written."""
        return self.id == "specs" and change.skip_specs

    def exists(self, change: Change) -> bool:
        if any(ch in self.generates for ch in "*?["):
            return any(p.is_file() for p in change.path.glob(self.generates))
        return (change.path / self.generates).is_file()


class WorkflowError(SpecworksError):
    """Raised for unknown artifacts."""


@dataclass(frozen=True)
class CheckArtifact:
    """An artifact that holds findings (review.md, validation.md), as the schema declares it.

    ``letter`` starts its finding IDs (``R1``, ``V1``), ``phase`` is the step that closes its findings and names the
    skill of its checks (``/specworks-<phase>``), and ``blocks`` are the gates its open findings fail.
    Implements REQ-FLOW-018.
    """

    id: str
    file: str
    letter: str
    phase: str
    blocks: tuple[str, ...]


# @req REQ-FLOW-018
def _declared(artifacts: dict[str, Artifact]) -> list[CheckArtifact]:
    """The artifacts with a ``findings`` entry, as check artifacts in schema order; a letter used twice raises ``WorkflowError``."""
    found: list[CheckArtifact] = []
    for art in artifacts.values():
        if art.findings is None:
            continue
        letter = str(art.findings["letter"]).upper()
        if clash := next((other for other in found if other.letter == letter), None):
            raise WorkflowError(f"check artifacts {clash.id} and {art.id} both use the finding letter {letter!r} in schema.yaml")
        found.append(CheckArtifact(id=art.id, file=art.generates, letter=letter, phase=art.phase, blocks=tuple(art.findings.get("blocks", ()))))
    return found


# @req REQ-FLOW-018
def check_artifacts() -> list[CheckArtifact]:
    """The check artifacts of the schema, in schema order; a letter used twice raises ``WorkflowError`` when the schema loads.

    Implements REQ-FLOW-018.
    """
    return _declared(load_artifacts())


# @req REQ-FLOW-018
def check_artifact(artifact_id: str) -> CheckArtifact:
    """The check artifact with this id; ``WorkflowError`` naming the check artifacts for any other.

    Implements REQ-FLOW-018, REQ-FLOW-016.
    """
    declared = check_artifacts()
    found = next((a for a in declared if a.id == artifact_id.strip().lower()), None)
    if found is None:
        raise WorkflowError(f"{artifact_id.strip()!r} is not a check artifact; one of {', '.join(a.id for a in declared)}")
    return found


# @req REQ-FLOW-018
def check_artifact_for(finding_id: str) -> CheckArtifact:
    """The check artifact a finding ID belongs to, by its letter (``V3`` -> validation); ``WorkflowError`` for an ID whose
    letter is no check artifact's.

    Implements REQ-FLOW-016, REQ-FLOW-018.
    """
    declared = check_artifacts()
    match = re.fullmatch(r"(?P<letter>[A-Za-z])\d+", finding_id.strip())
    found = next((a for a in declared if match and a.letter == match.group("letter").upper()), None)
    if found is None:
        letters = ", ".join(f"{a.letter}<n> in {a.file}" for a in declared)
        raise WorkflowError(f"{finding_id.strip()!r} is not the ID of a finding of a check artifact ({letters})")
    return found


@cache
def load_artifacts() -> dict[str, Artifact]:
    text = resources.files("specworks").joinpath("schema.yaml").read_text(encoding="utf-8")
    raw = yaml.safe_load(text)
    artifacts = {item["id"]: Artifact(**item) for item in raw["artifacts"]}
    _declared(artifacts)  # a letter used twice fails here, when the schema loads (REQ-FLOW-018)
    return artifacts


def read_template(name: str) -> str:
    if not name:
        return ""
    return resources.files("specworks").joinpath("templates", name).read_text(encoding="utf-8")


# @req REQ-FLOW-001
def artifact_states(change: Change) -> list[dict]:
    """Each artifact as done, ready (all requirements exist), blocked, or skipped (specs of a skip_specs change)."""
    artifacts = load_artifacts()
    states = []
    for art in artifacts.values():
        if art.exists(change):
            status = "done"
        elif art.skipped(change):
            status = "skipped"
        else:
            missing = [r for r in art.requires if not (artifacts[r].exists(change) or artifacts[r].optional or artifacts[r].skipped(change))]
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


# @req REQ-FLOW-001
def half_progress(change: Change) -> dict[str, dict[str, int]] | None:
    """Each half's tasks done and in total (``{"test": {"done": 3, "total": 3}, "code": {...}}``) for a change in implement, else None.

    Read from tasks.md only, without running any command.
    """
    if change.phase != "implement":
        return None
    path = change.path / TASKS_FILE
    tasks = parse_tasks(read_text(path))[0] if path.is_file() else []
    return {
        half: {"done": sum(t.done for t in tasks if t.half == half), "total": sum(t.half == half for t in tasks)}
        for half in HALVES
    }


# @req REQ-FLOW-002
def instructions(ws: Workspace, module: Module, change: Change, artifact_id: str) -> dict:
    artifacts = load_artifacts()
    if artifact_id not in artifacts:
        raise WorkflowError(f"unknown artifact '{artifact_id}'; expected one of {', '.join(artifacts)}")
    art = artifacts[artifact_id]
    data = {
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
    if art.id == "specs":
        # Where each delta goes and which IDs to use; new capabilities: `specworks spec show <ref>`.
        touched = []
        for path in delta_files(change):
            try:
                touched.append(resolve_delta(ws, change, path).ref)
            except ConfigError:  # reported by `specworks check`
                continue
        data["capabilities"] = [describe(ws, cap, with_scenarios=False) for cap in workspace_capabilities(ws)]
        data["writtenDeltas"] = touched
    return data
