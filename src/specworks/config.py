"""Project configuration: locating the project root and reading its config file.

A project is a folder holding ``<dir>.yml`` next to the workflow folder
``<dir>/`` (e.g. ``spec.yml`` + ``spec/``). The file name defines the folder
name; the first line ``specworks: 1`` marks the file as a specworks config so
an unrelated ``docs.yml`` is never mistaken for one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import yaml

CONFIG_EXT = ".yml"
CONFIG_VERSION = 1
MARKER_RE = re.compile(r"^specworks:[ \t]*\d+[ \t]*(#.*)?$", re.MULTILINE)
DEFAULT_DIR = "specworks"
DIR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
DEFAULT_DOCS_DIR = "docs"
MAX_CONTEXT_BYTES = 50 * 1024
MODULE_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PREFIX_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*$")


class ConfigError(Exception):
    """Raised when a config file is missing or invalid."""


@dataclass
class Capability:
    """A durable system behaviour, owned by a folder of code.

    Its living docs (spec, requirements, design, architecture) live in
    ``<path>/<docs_dir>/`` next to the code that implements it.
    """

    name: str
    path: str
    description: str = ""
    prefix: str = ""  # requirement ID prefix (REQ-<prefix>-001); derived from the name when empty

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
class DiagramSettings:
    """How `specworks diagrams` renders D2 sources; set once at the top level for one shared look."""

    theme: int = 0  # D2 theme ID (`d2 themes`): 0 Neutral Default
    dark_theme: int | None = 200  # used when the viewer is in dark mode; None = same as theme
    layout: str = "elk"  # elk (clean orthogonal routing) or dagre
    sketch: bool = False  # hand-drawn look
    pad: int = 24


def load_diagram_settings(raw: object) -> DiagramSettings:
    if raw is None:
        return DiagramSettings()
    if not isinstance(raw, dict):
        raise ConfigError("'diagrams' must be a mapping (theme, dark_theme, layout, sketch, pad)")
    unknown = set(raw) - {"theme", "dark_theme", "layout", "sketch", "pad"}
    if unknown:
        raise ConfigError(f"'diagrams' has unknown keys: {', '.join(sorted(unknown))}")
    settings = DiagramSettings(**raw)
    if not isinstance(settings.theme, int) or not (settings.dark_theme is None or isinstance(settings.dark_theme, int)):
        raise ConfigError("'diagrams.theme' and 'diagrams.dark_theme' are D2 theme numbers (see `d2 themes`)")
    if settings.layout not in ("elk", "dagre"):
        raise ConfigError("'diagrams.layout' must be elk or dagre")
    if not isinstance(settings.sketch, bool) or not isinstance(settings.pad, int) or settings.pad < 0:
        raise ConfigError("'diagrams.sketch' must be true/false and 'diagrams.pad' a non-negative number")
    return settings


@dataclass
class Config:
    root: Path
    context: str = ""
    dir: str = DEFAULT_DIR  # taken from the config file name: spec.yml -> spec
    docs_dir: str = DEFAULT_DOCS_DIR
    capabilities: dict[str, Capability] = field(default_factory=dict)
    modules: dict[str, str] = field(default_factory=dict)
    test_globs: list[str] = field(default_factory=list)
    source_globs: list[str] = field(default_factory=list)
    diagrams: DiagramSettings = field(default_factory=DiagramSettings)

    @property
    def config_path(self) -> Path:
        return self.root / config_name(self.dir)

    @property
    def changes_dir(self) -> str:
        return f"{self.dir}/changes"

    @property
    def changes_path(self) -> Path:
        return self.root / self.changes_dir

    @property
    def archive_path(self) -> Path:
        return self.changes_path / "archive"


def config_name(dir: str) -> str:
    return f"{dir}{CONFIG_EXT}"


def is_config_file(path: Path) -> bool:
    try:
        return path.is_file() and MARKER_RE.search(path.read_text(encoding="utf-8")) is not None
    except (OSError, UnicodeDecodeError):
        return False


def find_config(directory: Path) -> Path | None:
    """The specworks config in ``directory`` (any ``*.yml`` with the marker), if there is one."""
    if not directory.is_dir():
        return None
    found = [p for p in sorted(directory.glob(f"*{CONFIG_EXT}")) if is_config_file(p)]
    if len(found) > 1:
        names = ", ".join(p.name for p in found)
        raise ConfigError(f"{directory} has several specworks configs ({names}); keep only one")
    return found[0] if found else None


def find_root(start: Path | None = None) -> Path | None:
    """Walk up from ``start`` until a directory holding a specworks config is found."""
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        if find_config(directory) is not None:
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
    """The workflow folder is a single folder name; it also names the config file (<dir>.yml)."""
    if not isinstance(value, str) or not DIR_RE.match(value.strip()):
        raise ConfigError(
            f"folder name must be a single name of letters, digits, '-' or '_' (e.g. spec, docs, context), got '{value}'"
        )
    return value.strip()


def validate_module_name(name: object) -> str:
    if not isinstance(name, str) or not MODULE_NAME_RE.match(name):
        raise ConfigError(f"module name '{name}' must be kebab-case (e.g. billing, user-service)")
    return name


def load_config(root: Path, dir: str | None = None) -> Config:
    """Load ``root/<dir>.yml``, or the only specworks config in ``root`` when ``dir`` is None."""
    if dir is not None:
        path = root / config_name(validate_dir(dir))
        if not is_config_file(path):
            raise ConfigError(f"{path} is not a specworks config (missing or no 'specworks: {CONFIG_VERSION}' line)")
    else:
        found = find_config(root)
        if found is None:
            raise ConfigError(f"no specworks config (<dir>{CONFIG_EXT}) in {root}")
        path = found
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a YAML mapping")
    if raw.get("specworks") != CONFIG_VERSION:
        raise ConfigError(f"{path}: unsupported config version specworks: {raw.get('specworks')!r} (expected {CONFIG_VERSION})")
    if "dir" in raw:
        raise ConfigError(
            f"{path}: 'dir' is no longer a setting; the file name sets the folder ({path.name} -> {path.stem}/). Remove it."
        )

    context = raw.get("context") or ""
    if not isinstance(context, str):
        raise ConfigError("'context' must be a string")
    if len(context.encode("utf-8")) > MAX_CONTEXT_BYTES:
        raise ConfigError(f"'context' is larger than {MAX_CONTEXT_BYTES} bytes")

    capabilities = {}
    for name, value in (raw.get("capabilities") or {}).items():
        if not isinstance(name, str) or not MODULE_NAME_RE.match(name):
            raise ConfigError(f"capability name '{name}' must be kebab-case (e.g. user-auth)")
        if isinstance(value, str):
            value = {"path": value}
        if not isinstance(value, dict) or "path" not in value:
            raise ConfigError(f"capability '{name}' needs a 'path'")
        prefix = str(value.get("prefix", "") or "")
        if prefix and not PREFIX_RE.match(prefix):
            raise ConfigError(f"capability '{name}': prefix '{prefix}' must be upper-case letters/digits (e.g. AUTH)")
        capabilities[name] = Capability(
            name=name,
            path=validate_relative(str(value["path"]).rstrip("/"), f"capability '{name}' path"),
            description=str(value.get("description", "")),
            prefix=prefix,
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
        dir=validate_dir(path.stem),
        docs_dir=raw.get("docs_dir", DEFAULT_DOCS_DIR),
        capabilities=capabilities,
        modules=modules,
        test_globs=list(raw.get("test_globs") or []),
        source_globs=list(raw.get("source_globs") or []),
        diagrams=load_diagram_settings(raw.get("diagrams")),
    )


DEFAULT_CONFIG = """\
specworks: 1
# specworks configuration. The file name sets the workflow folder:
# spec.yml -> spec/changes/ (in-flight changes) and spec/changes/archive/.
# Modules (sub-projects) use the same file and folder name as the top level.
#
# context: free text the agent reads before every phase (stack, conventions,
# constraints). Keep it short; it is guidance, not documentation.
context: |

# Name of the folder, inside each capability's code path, that holds its
# living docs (spec.md, requirements.md, design.md, architecture.md).
docs_dir: docs

# Capabilities: durable behaviours of the system and the code folder that owns
# each one. `close` writes the capability's living docs into <path>/<docs_dir>/.
# Requirement IDs are REQ-<prefix>-NNN; the prefix defaults to the capability
# name in upper case (with the module name in front inside a module).
# capabilities:
#   user-auth:
#     path: src/auth
#     description: Login, sessions and password reset
#     prefix: AUTH          # optional: REQ-AUTH-001 instead of REQ-USER-AUTH-001
capabilities: {}

# Modules: sub-projects with their own config (same file name as this one),
# like git submodules. Each one is a complete project (own context,
# capabilities and changes) linked to this one. Add them with `specworks module add <path>`.
# modules:
#   billing: services/billing
modules: {}

# Globs used by `specworks trace` to find tests and source files. Empty means
# "scan everything that is not in the workflow folder".
test_globs: []
source_globs: []

# Design diagrams are written in D2 (https://d2lang.com) and rendered to SVG
# by `specworks diagrams`. The top-level settings apply to the whole workspace.
# Themes: `d2 themes` (0 Neutral Default, 1 Neutral Grey, 4 Cool Classics,
# 8 Colorblind Clear, 303 C4; dark: 200 Dark Mauve, 201 Dark Flagship).
diagrams:
  theme: 0
  dark_theme: 200
  layout: elk
  sketch: false
"""


def write_default_config(root: Path, dir: str) -> Path:
    path = root / config_name(validate_dir(dir))
    path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return path


def add_module_entry(root: Path, name: str, path: str) -> None:
    """Add ``name: path`` under ``modules:`` in the project's config, keeping the user's comments.

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

    config_file = cfg.config_path
    lines = config_file.read_text(encoding="utf-8").splitlines()
    entry = f"  {name}: {path}"
    for i, line in enumerate(lines):
        if re.match(r"^modules:\s*(\{\s*\})?\s*(#.*)?$", line):
            lines[i] = "modules:"
            # Append after the last indented entry of the block, keeping the order of addition.
            end = i + 1
            while end < len(lines) and (lines[end].startswith((" ", "\t")) or not lines[end].strip()):
                end += 1
            while end > i + 1 and not lines[end - 1].strip():
                end -= 1
            lines.insert(end, entry)
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
