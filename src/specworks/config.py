"""Project configuration: locating the project root and reading specworks.yaml."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import yaml

CONFIG_FILE = "specworks.yaml"
DEFAULT_DIR = "specworks"
DEFAULT_DOCS_DIR = "docs"
MAX_CONTEXT_BYTES = 50 * 1024
MODULE_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


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
    dir: str = DEFAULT_DIR
    docs_dir: str = DEFAULT_DOCS_DIR
    capabilities: dict[str, Capability] = field(default_factory=dict)
    modules: dict[str, str] = field(default_factory=dict)
    test_globs: list[str] = field(default_factory=list)
    source_globs: list[str] = field(default_factory=list)

    @property
    def changes_dir(self) -> str:
        return f"{self.dir}/changes"

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


def validate_relative(value: object, what: str) -> str:
    """A plain relative path that stays inside the project folder."""
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{what} must be a non-empty folder name")
    path = PurePosixPath(value.strip().replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or str(path) == ".":
        raise ConfigError(f"{what} must be a relative folder inside the project, got '{value}'")
    return str(path)


def validate_dir(value: object) -> str:
    return validate_relative(value, "'dir'")


def validate_module_name(name: object) -> str:
    if not isinstance(name, str) or not MODULE_NAME_RE.match(name):
        raise ConfigError(f"module name '{name}' must be kebab-case (e.g. billing, user-service)")
    return name


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

    raw_modules = raw.get("modules") or {}
    if not isinstance(raw_modules, dict):
        raise ConfigError("'modules' must be a mapping of name: path")
    modules = {
        validate_module_name(name): validate_relative(path, f"module '{name}' path")
        for name, path in raw_modules.items()
    }

    return Config(
        root=root,
        context=context,
        dir=validate_dir(raw.get("dir", DEFAULT_DIR)),
        docs_dir=raw.get("docs_dir", DEFAULT_DOCS_DIR),
        capabilities=capabilities,
        modules=modules,
        test_globs=list(raw.get("test_globs") or []),
        source_globs=list(raw.get("source_globs") or []),
    )


DEFAULT_CONFIG_TEMPLATE = """\
# specworks configuration
#
# context: free text the agent reads before every phase (stack, conventions,
# constraints). Keep it short; it is guidance, not documentation.
context: |

# Workflow folder (relative to this file), e.g. specworks, spec, docs, context.
# In-flight changes live in <dir>/changes/, finished ones in <dir>/changes/archive/.
dir: {dir}

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

# Modules: sub-projects with their own specworks.yaml, like git submodules.
# Each one is a complete project (own dir, context, capabilities and changes)
# linked to this one. Add them with `specworks module add <path>`.
# modules:
#   billing: services/billing
modules: {}

# Globs used by `specworks trace` to find tests and source files. Empty means
# "scan everything that is not in the workflow folder".
test_globs: []
source_globs: []
"""


def default_config(dir: str = DEFAULT_DIR) -> str:
    return DEFAULT_CONFIG_TEMPLATE.replace("{dir}", validate_dir(dir))


def add_module_entry(root: Path, name: str, path: str) -> None:
    """Add ``name: path`` under ``modules:`` in root/specworks.yaml, keeping the user's comments.

    The file is edited as text (a YAML dump would drop comments) and re-read to
    make sure the edit produced the expected mapping.
    """
    validate_module_name(name)
    path = validate_relative(path, f"module '{name}' path")
    cfg = load_config(root)
    if name in cfg.modules:
        raise ConfigError(f"module '{name}' already exists ({cfg.modules[name]})")
    for other, other_path in cfg.modules.items():
        if other_path == path:
            raise ConfigError(f"{path} is already linked as module '{other}'")

    config_file = root / CONFIG_FILE
    lines = config_file.read_text(encoding="utf-8").splitlines()
    entry = f"  {name}: {path}"
    for i, line in enumerate(lines):
        match = re.match(r"^modules:\s*(\{\s*\})?\s*(#.*)?$", line)
        if match:
            lines[i] = "modules:"
            lines.insert(i + 1, entry)
            break
    else:
        lines += ["", "modules:", entry]
    original = config_file.read_text(encoding="utf-8")
    config_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    try:
        updated = load_config(root).modules
    except ConfigError:
        updated = {}
    if updated.get(name) != path:
        config_file.write_text(original, encoding="utf-8")
        raise ConfigError(
            f"could not add the module to {config_file} automatically; add it by hand:\nmodules:\n{entry}"
        )
