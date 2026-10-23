"""In-flight changes: creation, listing and phase tracking."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from .config import Config
from .errors import SpecworksError
from .validators import validate_kebab

META_FILE = ".change.yaml"
ARCHIVE_DIR = "archive"
ACTIVE_DIR = "active"
ARCHIVED_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})-(?P<name>.+)$")  # <archive>/<date>-<name>/
# Each phase is driven by the skill of the same name (specworks-<phase>); `close`
# writes the living docs and archives the change, which then reads `done`.
PHASES = ("refine", "specify", "design", "implement", "review", "validate", "close", "done")
# The two halves of the implement phase: names of gates, review steps and task markers, not phases (REQ-PROJ-011).
HALVES = ("test", "code")


def half_error(half: str) -> str:
    return f"'{half}' is not a phase: `test` and `code` are the halves of `implement`"


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
    abandoned: str = ""  # why it was archived without merging (specworks abandon)
    specified: dict[str, str] = field(default_factory=dict)  # requirement ID -> fingerprint when specify last passed

    @property
    def order(self) -> tuple[str, str, str]:
        """Sorts changes by when they started; the name and folder break ties."""
        return (self.created, self.name, self.path.as_posix())

    def save(self) -> None:
        data: dict[str, object] = {"name": self.name, "created": self.created, "phase": self.phase}
        if self.skip_specs:
            data["skip_specs"] = True
        if self.abandoned:
            data["abandoned"] = self.abandoned
        if self.specified:
            data["specified"] = dict(self.specified)
        (self.path / META_FILE).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


# @req REQ-PROJ-010
def create_change(cfg: Config, name: str) -> Change:
    validate_kebab(name, "change name", "add-user-auth")
    if name in (ARCHIVE_DIR, ACTIVE_DIR):
        raise ChangeError(f"'{name}' is reserved for the changes folders; pick another name")
    if archived := archived_as(cfg, name):
        raise ChangeError(
            f"change '{name}' was archived at {archived.path.relative_to(cfg.root).as_posix()}; "
            "requirements.md History refers to it by name, so pick another one"
        )
    path = cfg.changes_path / name
    if path.exists():
        raise ChangeError(f"change '{name}' already exists at {path.relative_to(cfg.root)}")
    path.mkdir(parents=True)
    change = Change(name=name, path=path, created=datetime.now().isoformat(timespec="seconds"))
    change.save()
    return change


# @req REQ-PROJ-011
def _read_change(path: Path, name: str, where: str) -> Change:
    try:
        meta = yaml.safe_load((path / META_FILE).read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ChangeError(f"cannot read {where}: {exc}") from None
    if not isinstance(meta, dict):
        raise ChangeError(f"{where} must be a mapping (name, created, phase), got {type(meta).__name__}")
    phase = meta.get("phase", "refine")
    if phase in HALVES:
        phase = "implement"  # saved before implement replaced the test and code phases
    if phase not in PHASES:
        raise ChangeError(f"change '{name}' has unknown phase '{phase}' in {where}; expected one of {', '.join(PHASES)}")
    return Change(
        name=name,
        path=path,
        phase=phase,
        created=str(meta.get("created", "")),
        skip_specs=bool(meta.get("skip_specs", False)),
        abandoned=str(meta.get("abandoned") or ""),
        specified={str(k): str(v) for k, v in specified.items()} if isinstance(specified := meta.get("specified"), dict) else {},
    )


# @req REQ-PROJ-020
def load_change(cfg: Config, name: str) -> Change:
    validate_kebab(name, "change name", "add-user-auth")
    path = cfg.changes_path / name
    if not (path / META_FILE).is_file():
        raise ChangeNotFound(f"change '{name}' not found in {cfg.changes_dir}")
    return _read_change(path, name, f"{cfg.changes_dir}/{name}/{META_FILE}")


# @req REQ-PROJ-020
def list_changes(cfg: Config) -> list[Change]:
    if not cfg.changes_path.is_dir():
        return []
    return [
        load_change(cfg, entry.name)
        for entry in sorted(cfg.changes_path.iterdir())
        if entry.is_dir() and (entry / META_FILE).is_file()
    ]


# @req REQ-PROJ-012
def list_archived(cfg: Config) -> list[Change]:
    """Closed and abandoned changes, oldest first; a folder whose metadata cannot be read is left out."""
    if not cfg.archive_path.is_dir():
        return []
    found = []
    for entry in sorted(cfg.archive_path.iterdir()):
        if not (entry.is_dir() and (match := ARCHIVED_RE.match(entry.name)) and (entry / META_FILE).is_file()):
            continue
        try:
            found.append(_read_change(entry, match.group("name"), f"{cfg.archive_dir}/{entry.name}/{META_FILE}"))
        except ChangeError:
            continue
    return found


def archived_as(cfg: Config, name: str) -> Change | None:
    """The newest archived change named ``name`` (or the archived one whose folder is ``name``), if any."""
    found = [c for c in list_archived(cfg) if name in (c.name, c.path.name)]
    return found[-1] if found else None


# @req REQ-PROJ-011
def set_phase(change: Change, phase: str) -> None:
    if phase in HALVES:
        raise ChangeError(half_error(phase))
    if phase not in PHASES:
        raise ChangeError(f"unknown phase '{phase}'; expected one of {', '.join(PHASES)}")
    if phase == "done":
        # `done` means merged into the living specs and archived; only `specworks close` does that.
        raise ChangeError("a change becomes done only through `specworks close`, which merges its specs and archives it")
    change.phase = phase
    change.save()
