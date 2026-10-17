"""Project configuration: locating the project root and reading its config file.

A project is a folder holding ``<dir>.yml`` next to the workflow folder
``<dir>/`` (e.g. ``spec.yml`` + ``spec/``). The file name defines the folder
name; the first line ``specworks: 1`` marks the file as a specworks config so
an unrelated ``docs.yml`` is never mistaken for one.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import pyd2
import yaml
from pyd2 import LAYOUTS, THEMES

from .errors import ConfigError
from .validators import check_keys, validate_capability_name, validate_dir, validate_module_name, validate_prefix, validate_relative

CONFIG_EXT = ".yml"
CONFIG_VERSION = 1
MARKER_RE = re.compile(r"^specworks:[ \t]*\d+[ \t]*(#.*)?$", re.MULTILINE)
DEFAULT_DIR = "specworks"
DEFAULT_DOCS_DIR = "docs"
MAX_CONTEXT_BYTES = 50 * 1024
CONFIG_KEYS = ("specworks", "context", "docs_dir", "capabilities", "modules", "test_globs", "source_globs", "commands", "diagrams")
CAPABILITY_KEYS = ("path", "prefix", "description")
DIAGRAM_KEYS = ("theme", "dark_theme", "layout", "sketch", "pad")


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


def theme_id(value: object, key: str) -> int:
    """A theme given by name (``c4``, ``Colorblind Clear``) or number -> its D2 number."""
    try:
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            raise ValueError(value)
        return pyd2.theme_id(value)
    except ValueError:
        raise ConfigError(f"'{key}': unknown theme {value!r}; use a name ({', '.join(THEMES)}) or a number from `d2 themes`") from None


def dark_theme_id(value: object, key: str) -> int | None:
    """Like ``theme_id``; ``none`` (or ``same``) means the light theme is used in dark mode too."""
    if value is None or (isinstance(value, str) and value.strip().lower() in ("none", "same")):
        return None
    try:
        return theme_id(value, key)
    except ConfigError as exc:
        raise ConfigError(f"{exc}, or none to use the light theme in dark mode too") from None


def theme_name(number: int | None) -> str:
    return "none" if number is None else pyd2.theme_name(number)


@dataclass
class DiagramSettings:
    """How `specworks diagrams` renders D2 sources; set once at the top level for one shared look."""

    theme: int = 0  # D2 theme ID (`d2 themes`): 0 Neutral Default
    dark_theme: int | None = 200  # used when the viewer is in dark mode; None = same as theme
    layout: str = "elk"  # elk (clean orthogonal routing) or dagre
    sketch: bool = False  # hand-drawn look
    pad: int = 24

    def options(self) -> pyd2.Options:
        """The pyd2 render options for these settings (version left out of the SVG)."""
        return pyd2.Options(self.theme, self.dark_theme, self.layout, self.sketch, self.pad, omit_version=True)


COMMAND_KEYS = ("test", "lint", "typecheck", "build", "format")


def load_commands(raw: object) -> dict[str, str]:
    """Shell commands the skills run (tests, lint, ...); empty values are left out."""
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ConfigError(f"'commands' must be a mapping of {', '.join(COMMAND_KEYS)} to shell commands")
    check_keys(raw, COMMAND_KEYS, "'commands'")
    commands = {}
    for key, value in raw.items():
        if value is None or value == "":
            continue
        if not isinstance(value, str):
            raise ConfigError(f"'commands.{key}' must be a shell command string")
        commands[key] = value.strip()
    return commands


def load_globs(raw: object, key: str) -> list[str]:
    """A list of glob strings; a single string is a common slip, so it gets its own message."""
    if raw is None:
        return []
    if isinstance(raw, str):
        raise ConfigError(f"'{key}' must be a list of globs, e.g. {key}: [{json.dumps(raw)}]")
    if not isinstance(raw, list) or not all(isinstance(g, str) and g.strip() for g in raw):
        raise ConfigError(f"'{key}' must be a list of glob strings")
    # Only *, ? and ** are wildcards; a [set] or {a,b} would be matched as plain text, so never match.
    if unsupported := [g for g in raw if any(ch in g for ch in "[]{}")]:
        raise ConfigError(f"'{key}': {', '.join(unsupported)}: globs support *, ? and ** only; list each pattern instead of [..] or {{..}}")
    return [g.strip() for g in raw]


def load_diagram_settings(raw: object) -> DiagramSettings:
    if raw is None:
        return DiagramSettings()
    if not isinstance(raw, dict):
        raise ConfigError("'diagrams' must be a mapping (theme, dark_theme, layout, sketch, pad)")
    check_keys(raw, DIAGRAM_KEYS, "'diagrams'")
    settings = DiagramSettings(**raw)  # themes by name or number, resolved below; the defaults are numbers already
    settings.theme = theme_id(settings.theme, "diagrams.theme")
    settings.dark_theme = dark_theme_id(settings.dark_theme, "diagrams.dark_theme")
    if settings.layout not in LAYOUTS:
        raise ConfigError("'diagrams.layout' must be elk or dagre")
    if not isinstance(settings.sketch, bool) or isinstance(settings.pad, bool) or not isinstance(settings.pad, int) or settings.pad < 0:
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
    commands: dict[str, str] = field(default_factory=dict)
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
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a YAML mapping")
    if raw.get("specworks") != CONFIG_VERSION:
        raise ConfigError(f"{path}: unsupported config version specworks: {raw.get('specworks')!r} (expected {CONFIG_VERSION})")
    if "dir" in raw:
        raise ConfigError(
            f"{path}: 'dir' is no longer a setting; the file name sets the folder ({path.name} -> {path.stem}/). Remove it."
        )
    check_keys(raw, CONFIG_KEYS, str(path))

    context = raw.get("context") or ""
    if not isinstance(context, str):
        raise ConfigError("'context' must be a string")
    if len(context.encode("utf-8")) > MAX_CONTEXT_BYTES:
        raise ConfigError(f"'context' is larger than {MAX_CONTEXT_BYTES} bytes")

    raw_capabilities = raw.get("capabilities") or {}
    if not isinstance(raw_capabilities, dict):
        raise ConfigError("'capabilities' must be a mapping of name: path (or name: {path, prefix, description})")
    capabilities = {}
    for name, value in raw_capabilities.items():
        validate_capability_name(name)
        if isinstance(value, str):
            value = {"path": value}
        if not isinstance(value, dict) or not isinstance(value.get("path"), str):
            raise ConfigError(f"capability '{name}' needs a 'path'")
        check_keys(value, CAPABILITY_KEYS, f"capability '{name}'")
        prefix = validate_prefix(str(value.get("prefix") or ""), f"capability '{name}': ")
        capabilities[name] = Capability(
            name=name,
            path=validate_relative(value["path"].rstrip("/"), f"capability '{name}' path"),
            description=str(value.get("description") or ""),
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
        # Joined to each capability's path, so it must stay inside it.
        docs_dir=validate_relative(raw.get("docs_dir", DEFAULT_DOCS_DIR), "'docs_dir'"),
        capabilities=capabilities,
        modules=modules,
        test_globs=load_globs(raw.get("test_globs"), "test_globs"),
        source_globs=load_globs(raw.get("source_globs"), "source_globs"),
        commands=load_commands(raw.get("commands")),
        diagrams=load_diagram_settings(raw.get("diagrams")),
    )
