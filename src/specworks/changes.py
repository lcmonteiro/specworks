"""In-flight changes: creation, listing and phase tracking."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from .config import Config

META_FILE = ".change.yaml"
# Each phase is driven by the skill of the same name (specworks-<phase>); `close`
# writes the living docs and archives the change, which then reads `done`.
PHASES = ("refine", "propose", "test", "implement", "review", "verify", "close", "done")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ChangeError(Exception):
    """Raised for invalid change names or missing changes."""


@dataclass
class Change:
    name: str
    path: Path
    phase: str = "refine"
    created: str = ""
    skip_specs: bool = False

    def save(self) -> None:
        data = {"name": self.name, "created": self.created, "phase": self.phase}
        if self.skip_specs:
            data["skip_specs"] = True
        (self.path / META_FILE).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def validate_name(name: str) -> None:
    if not NAME_RE.match(name):
        raise ChangeError(f"change name '{name}' must be kebab-case (e.g. add-user-auth)")


def create_change(cfg: Config, name: str) -> Change:
    validate_name(name)
    path = cfg.changes_path / name
    if path.exists():
        raise ChangeError(f"change '{name}' already exists at {path.relative_to(cfg.root)}")
    path.mkdir(parents=True)
    change = Change(name=name, path=path, created=date.today().isoformat())
    change.save()
    return change


def load_change(cfg: Config, name: str) -> Change:
    path = cfg.changes_path / name
    meta_file = path / META_FILE
    if name == "archive" or not meta_file.is_file():
        raise ChangeError(f"change '{name}' not found in {cfg.changes_dir}")
    meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
    phase = meta.get("phase", "refine")
    if phase not in PHASES:
        raise ChangeError(f"change '{name}' has unknown phase '{phase}'")
    return Change(
        name=name,
        path=path,
        phase=phase,
        created=str(meta.get("created", "")),
        skip_specs=bool(meta.get("skip_specs", False)),
    )


def list_changes(cfg: Config) -> list[Change]:
    if not cfg.changes_path.is_dir():
        return []
    return [
        load_change(cfg, entry.name)
        for entry in sorted(cfg.changes_path.iterdir())
        if entry.is_dir() and entry.name != "archive" and (entry / META_FILE).is_file()
    ]


def set_phase(change: Change, phase: str) -> None:
    if phase not in PHASES:
        raise ChangeError(f"unknown phase '{phase}'; expected one of {', '.join(PHASES)}")
    change.phase = phase
    change.save()
