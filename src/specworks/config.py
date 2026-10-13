"""Project configuration: locating the project root and reading specworks.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_FILE = "specworks.yaml"
DEFAULT_CHANGES_DIR = "specworks/changes"
DEFAULT_DOCS_DIR = "docs"
MAX_CONTEXT_BYTES = 50 * 1024


class ConfigError(Exception):
    """Raised when specworks.yaml is missing or invalid."""


@dataclass
class Capability:
    """A durable system behaviour, owned by a folder of code.

    Its living docs (spec, requirements, design, architecture) live in
    ``<path>/<docs_dir>/`` next to the code that implements it.
    """

    name: str
    path: str
    description: str = ""

    def docs_path(self, root: Path, docs_dir: str) -> Path:
        return root / self.path / docs_dir

    def to_dict(self, root: Path, docs_dir: str) -> dict:
        docs = self.docs_path(root, docs_dir)
        return {
            "name": self.name,
            "path": self.path,
            "description": self.description,
            "docsPath": str(docs.relative_to(root)),
            "hasSpec": (docs / "spec.md").is_file(),
        }


@dataclass
class Config:
    root: Path
    context: str = ""
    changes_dir: str = DEFAULT_CHANGES_DIR
    docs_dir: str = DEFAULT_DOCS_DIR
    capabilities: dict[str, Capability] = field(default_factory=dict)
    test_globs: list[str] = field(default_factory=list)
    source_globs: list[str] = field(default_factory=list)

    @property
    def changes_path(self) -> Path:
        return self.root / self.changes_dir

    @property
    def archive_path(self) -> Path:
        return self.changes_path / "archive"


def find_root(start: Path | None = None) -> Path | None:
    """Walk up from ``start`` until a directory holding specworks.yaml is found."""
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        if (directory / CONFIG_FILE).is_file():
            return directory
    return None


def load_config(root: Path) -> Config:
    path = root / CONFIG_FILE
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a YAML mapping")

    context = raw.get("context") or ""
    if not isinstance(context, str):
        raise ConfigError("'context' must be a string")
    if len(context.encode("utf-8")) > MAX_CONTEXT_BYTES:
        raise ConfigError(f"'context' is larger than {MAX_CONTEXT_BYTES} bytes")

    capabilities = {}
    for name, value in (raw.get("capabilities") or {}).items():
        if isinstance(value, str):
            value = {"path": value}
        if not isinstance(value, dict) or "path" not in value:
            raise ConfigError(f"capability '{name}' needs a 'path'")
        capabilities[name] = Capability(
            name=name,
            path=str(value["path"]).rstrip("/"),
            description=str(value.get("description", "")),
        )

    return Config(
        root=root,
        context=context,
        changes_dir=raw.get("changes_dir", DEFAULT_CHANGES_DIR),
        docs_dir=raw.get("docs_dir", DEFAULT_DOCS_DIR),
        capabilities=capabilities,
        test_globs=list(raw.get("test_globs") or []),
        source_globs=list(raw.get("source_globs") or []),
    )


DEFAULT_CONFIG = """\
# specworks configuration
#
# context: free text the agent reads before every phase (stack, conventions,
# constraints). Keep it short; it is guidance, not documentation.
context: |

# Where in-flight changes live (relative to this file).
changes_dir: specworks/changes

# Name of the folder, inside each capability's code path, that holds its
# living docs (spec.md, requirements.md, design.md, architecture.md).
docs_dir: docs

# Capabilities: durable behaviours of the system and the code folder that owns
# each one. `done` writes the capability's living docs into <path>/<docs_dir>/.
# capabilities:
#   user-auth:
#     path: src/auth
#     description: Login, sessions and password reset
capabilities: {}

# Globs used by `specworks trace` to find tests and source files. Empty means
# "scan everything tracked that is not in changes_dir".
test_globs: []
source_globs: []
"""
