"""Writing the config file: the commented default written by `specworks init`, and entries
added by `specworks module add` / `specworks capability add` (comments and order kept)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from .config import COMMAND_KEYS, CONFIG_FILE, MAX_CONTEXT_BYTES, WORKFLOW_DIR, Config, ConfigError, load_config, theme_id, theme_name
from .files import read_text
from .validators import validate_capability_name, validate_module_name, validate_prefix, validate_relative

SETTABLE_KEYS: tuple[str, ...] = ("context", *(f"commands.{key}" for key in COMMAND_KEYS))
"""The keys `specworks config set` writes, in the order an error names them. Implements REQ-PROJ-025."""

DEFAULT_CONFIG = """\
specworks: 1
# specworks configuration. It always lives in .specworks/config.yml, and
# .specworks/ is the workflow folder: .specworks/changes/active/ (in-flight
# changes) and .specworks/changes/archive/. Every module has the same layout.
#
# context: free text the agent reads before every phase (stack, conventions,
# constraints). Keep it short; it is guidance, not documentation.
context: |

# Name of the folder, inside each capability's code path, that holds its
# living docs (spec.md, requirements.md, design.md and its diagrams).
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

# Modules: sub-projects with their own config (their own .specworks/config.yml),
# like git submodules. Each one is a complete project (own context,
# capabilities and changes) linked to this one. Add them with `specworks module add <path>`.
# modules:
#   billing: services/billing
modules: {}

# Globs used by `specworks trace` to find tests and source files, relative to
# the project folder (the one holding .specworks/); they apply to this project's files, not to its modules'.
# Empty means "scan everything that is not in the workflow folder", except
# documentation (.md, .rst, .txt, ...): a tag quoted in a doc is not code or a test.
# In a glob * and ? stay within one folder and ** spans any number of folders,
# e.g. test_globs: ["tests/**/*.py"] or source_globs: ["src/**"].
test_globs: []
source_globs: []

# Commands the skills run, in this project's own tooling (any language).
# A module's commands override the top level's, key by key.
#   test: uv run pytest            # or: npm test, go test ./..., cargo test, ctest
#   lint: uv run ruff check .
commands:
  test:
  lint:

# Design diagrams are written in D2 (https://d2lang.com) and rendered to SVG
# by `specworks diagrams`. Only the top-level settings are used, so every
# diagram in the workspace shares one look (modules ignore theirs).
# Themes by name or number - `specworks diagrams --themes` lists them, e.g.
# neutral-default, neutral-grey, cool-classics, colorblind-clear, c4, origami;
# dark mode: dark-mauve, dark-flagship-terrastruct, or none (same as theme).
diagrams:
  theme: neutral-default
  dark_theme: dark-mauve
  layout: elk           # elk or dagre
  sketch: false         # true for a hand-drawn look
"""


# @req REQ-PROJ-009
def write_default_config(root: Path, diagram_theme: str | None = None) -> Path:
    path = root / WORKFLOW_DIR / CONFIG_FILE
    text = DEFAULT_CONFIG
    if diagram_theme is not None:
        theme = theme_name(theme_id(diagram_theme, "--diagram-theme"))
        text = text.replace("  theme: neutral-default\n", f"  theme: {theme}\n", 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# @req REQ-PROJ-008
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

    _insert_entry(root, "modules", [f"  {name}: {path}"], lambda cfg: cfg.modules.get(name) == path)


# @req REQ-PROJ-008
def _insert_entry(root: Path, key: str, entry: list[str], applied) -> None:
    """Append ``entry`` lines to the ``key:`` block of the config as text (keeping comments), then re-read to check.

    The check also requires every entry already under ``key`` to survive: a block the
    text edit does not understand (e.g. ``capabilities: {auth: src/auth}``) would
    otherwise gain a second ``key:``, and YAML keeps only the last one.
    """
    cfg = load_config(root)
    before = dict(getattr(cfg, key))
    config_file = cfg.config_path
    original = read_text(config_file)
    lines = original.splitlines()
    pattern = re.compile(rf"^{key}:\s*(\{{\s*\}})?\s*(#.*)?$")
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = f"{key}:"
            # Append after the last indented line of the block, keeping the order of addition.
            end = i + 1
            while end < len(lines) and (lines[end].startswith((" ", "\t")) or not lines[end].strip()):
                end += 1
            while end > i + 1 and not lines[end - 1].strip():
                end -= 1
            lines[end:end] = entry
            break
    else:
        lines += ["", f"{key}:", *entry]
    config_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    try:
        after = load_config(root)
        kept = getattr(after, key)
        ok = applied(after) and all(kept.get(name) == value for name, value in before.items())
    except ConfigError:
        ok = False
    if not ok:
        config_file.write_text(original, encoding="utf-8")
        body = "\n".join(entry)
        raise ConfigError(f"could not add it to {config_file} automatically; add it by hand:\n{key}:\n{body}")


# @req REQ-PROJ-008
def add_capability_entry(root: Path, name: str, path: str, prefix: str = "", description: str = "") -> None:
    """Register a capability (name -> code path) in the config at ``root``, keeping the user's comments."""
    validate_capability_name(name)
    path = validate_relative(path, f"capability '{name}' path")
    validate_prefix(prefix)
    if name in load_config(root).capabilities:
        raise ConfigError(f"capability '{name}' already exists")
    entry = [f"  {name}:", f"    path: {path}"]
    if description:
        entry.append(f"    description: {json.dumps(description)}")
    if prefix:
        entry.append(f"    prefix: {prefix}")

    def applied(cfg: Config) -> bool:
        cap = cfg.capabilities.get(name)
        return cap is not None and cap.path == path and cap.prefix == prefix

    _insert_entry(root, "capabilities", entry, applied)


# @req REQ-PROJ-022
def save_tools(root: Path, ids: list[str]) -> None:
    """Save ``tools: [<ids>]`` in the config at ``root``, replacing a ``tools:`` entry already there and keeping comments.

    The file is edited as text and reloaded; when it does not load with those tools, it is
    restored and ``ConfigError`` says to set ``tools`` by hand.
    """
    entry = f"tools: [{', '.join(ids)}]"
    config_file = root / WORKFLOW_DIR / CONFIG_FILE
    original = read_text(config_file)
    lines = original.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^tools:", line):
            # A flow list stays on its line; a block list's items follow, indented or starting with "-".
            end = i + 1
            while end < len(lines) and lines[end].startswith((" ", "\t", "-")):
                end += 1
            lines[i:end] = [entry]
            break
    else:
        lines += ["", "# AI tools the skills are installed for (`specworks skills --tools` changes it).", entry]
    config_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    try:
        ok = load_config(root).tools == ids
    except ConfigError:
        ok = False
    if not ok:
        config_file.write_text(original, encoding="utf-8")
        raise ConfigError(f"could not save the tools in {WORKFLOW_DIR}/{CONFIG_FILE} automatically; set them by hand:\n{entry}")


# @req REQ-PROJ-025
def set_config_value(root: Path, key: str, value: str) -> None:
    """Set ``key`` (one of ``SETTABLE_KEYS``) to ``value`` in the config at ``root``, keeping the user's comments.

    An empty ``value`` clears the key. The file is edited as text and reloaded; when it does not
    load with just that key changed, it is restored. Raises ``ConfigError`` for an unknown key, a
    context over ``MAX_CONTEXT_BYTES``, or an edit that does not load back. Implements REQ-PROJ-025.
    """
    if key not in SETTABLE_KEYS:
        raise ConfigError(f"unknown config key '{key}'; use one of: {', '.join(SETTABLE_KEYS)}")
    expected: object
    if key == "context":
        text = value.replace("\r\n", "\n").rstrip("\n")
        expected = f"{text}\n" if text else ""  # `context: |` alone loads as an empty string
        if len(expected.encode("utf-8")) > MAX_CONTEXT_BYTES:
            raise ConfigError(f"'context' is larger than {MAX_CONTEXT_BYTES} bytes")
    config_file = load_config(root).config_path
    original = read_text(config_file)
    before = yaml.safe_load(original) or {}
    lines = original.splitlines()
    field = key
    if key == "context":
        _set_context(lines, text)
    else:
        field, name = key.split(".")
        _set_command(lines, name, value)
        commands = before.get(field)
        expected = {**(commands if isinstance(commands, dict) else {}), name: value or None}
    config_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    try:
        load_config(root)
        ok = yaml.safe_load(read_text(config_file)) == {**before, field: expected}
    except (ConfigError, yaml.YAMLError):
        ok = False
    if not ok:
        config_file.write_text(original, encoding="utf-8")
        raise ConfigError(f"could not set {key} in {WORKFLOW_DIR}/{CONFIG_FILE} automatically; set it by hand")


def _block_end(lines: list[str], start: int) -> int:
    """The end of the block whose header is ``lines[start]``: its indented and blank lines, without the trailing blank ones."""
    end = start + 1
    while end < len(lines) and (lines[end].startswith((" ", "\t")) or not lines[end].strip()):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    return end


# @req REQ-PROJ-025
def _set_command(lines: list[str], name: str, value: str) -> None:
    """Write ``name: value`` as one line of the ``commands:`` block, replacing that key's line or adding one."""
    entry = f"{name}:"
    if value:
        try:
            plain = yaml.safe_load(f"{name}: {value}") == {name: value}
        except yaml.YAMLError:
            plain = False
        entry += f" {value}" if plain else f" {json.dumps(value, ensure_ascii=False)}"
    header = re.compile(r"^commands:\s*(\{\s*\})?\s*(#.*)?$")
    for i, line in enumerate(lines):
        if match := header.match(line):
            lines[i] = f"commands: {match[2]}" if match[2] else "commands:"
            end = _block_end(lines, i)
            for j in range(i + 1, end):
                if found := re.match(rf"^([ \t]+){re.escape(name)}:(\s|$)", lines[j]):
                    lines[j] = found[1] + entry
                    return
            lines.insert(end, f"  {entry}")
            return
    lines += ["", "commands:", f"  {entry}"]


# @req REQ-PROJ-025
def _set_context(lines: list[str], text: str) -> None:
    """Write ``text`` as the ``context: |`` block, replacing the ``context:`` entry or adding one."""
    body = [f"  {line}" if line else "" for line in text.split("\n")] if text else []
    # A first line that starts with a space would set the block's indent: give it explicitly.
    entry = ["context: |2" if text.lstrip("\n").startswith(" ") else "context: |", *body]
    for i, line in enumerate(lines):
        if re.match(r"^context:", line):
            lines[i : _block_end(lines, i)] = entry
            return
    lines += ["", *entry]
