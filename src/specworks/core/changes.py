"""In-flight changes: creation, listing and phase tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from .config import Config
from .errors import SpecworksError
from .validators import validate_kebab

META_FILE = ".change.yaml"
# Each phase is driven by the skill of the same name (specworks-<phase>); `close`
# writes the living docs and archives the change, which then reads `done`.
PHASES = ("refine", "specify", "design", "test", "code", "review", "validate", "close", "done")
# Phase names before the rename; .change.yaml files that still use them load as the new names.
OLD_PHASES = {"propose": "specify", "interface": "design", "implement": "code", "verify": "validate"}


class ChangeError(SpecworksError):
    """Raised for invalid change names or missing changes."""


class ChangeNotFound(ChangeError):
    """Raised when no change of that name exists (a broken .change.yaml is a plain ChangeError)."""


@dataclass
class Change:
    name: str
    path: Path
    phase: str = "refine"
    created: str = ""
    skip_specs: bool = False

    @property
    def order(self) -> tuple[str, str, str]:
        """Sorts changes by when they started; the name and folder break ties."""
        return (self.created, self.name, self.path.as_posix())

    def save(self) -> None:
        data: dict[str, object] = {"name": self.name, "created": self.created, "phase": self.phase}
        if self.skip_specs:
            data["skip_specs"] = True
        (self.path / META_FILE).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def create_change(cfg: Config, name: str) -> Change:
    validate_kebab(name, "change name", "add-user-auth")
    path = cfg.changes_path / name
    if path.exists():
        raise ChangeError(f"change '{name}' already exists at {path.relative_to(cfg.root)}")
    path.mkdir(parents=True)
    change = Change(name=name, path=path, created=datetime.now().isoformat(timespec="seconds"))
    change.save()
    return change


def load_change(cfg: Config, name: str) -> Change:
    validate_kebab(name, "change name", "add-user-auth")  # also keeps refs out of archive/ and other folders
    path = cfg.changes_path / name
    meta_file = path / META_FILE
    if name == "archive" or not meta_file.is_file():
        raise ChangeNotFound(f"change '{name}' not found in {cfg.changes_dir}")
    where = f"{cfg.changes_dir}/{name}/{META_FILE}"
    try:
        meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ChangeError(f"cannot read {where}: {exc}") from None
    if not isinstance(meta, dict):
        raise ChangeError(f"{where} must be a mapping (name, created, phase), got {type(meta).__name__}")
    phase = meta.get("phase", "refine")
    phase = OLD_PHASES.get(phase, phase)
    if phase not in PHASES:
        raise ChangeError(f"change '{name}' has unknown phase '{phase}' in {where}; expected one of {', '.join(PHASES)}")
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
    if phase == "done":
        # `done` means merged into the living specs and archived; only `specworks close` does that.
        raise ChangeError("a change becomes done only through `specworks close`, which merges its specs and archives it")
    change.phase = phase
    change.save()
