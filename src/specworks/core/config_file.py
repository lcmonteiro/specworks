"""Writing the config file: the commented default written by `specworks init`, and entries
added by `specworks module add` / `specworks capability add` (comments and order kept)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .config import MODULE_NAME_RE, PREFIX_RE, Config, ConfigError, config_name, load_config, theme_id, theme_name, validate_dir, validate_module_name, validate_relative

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


def write_default_config(root: Path, dir: str, diagram_theme: str | None = None) -> Path:
    path = root / config_name(validate_dir(dir))
    text = DEFAULT_CONFIG
    if diagram_theme is not None:
        theme = theme_name(theme_id(diagram_theme, "--diagram-theme"))
        text = text.replace("  theme: neutral-default\n", f"  theme: {theme}\n", 1)
    path.write_text(text, encoding="utf-8")
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

    _insert_entry(root, "modules", [f"  {name}: {path}"], lambda cfg: cfg.modules.get(name) == path)


def _insert_entry(root: Path, key: str, entry: list[str], applied) -> None:
    """Append ``entry`` lines to the ``key:`` block of the config as text (keeping comments), then re-read to check.

    The check also requires every entry that was there before to be unchanged: a
    block the text edit does not understand (e.g. flow style ``key: {a: b}``)
    would otherwise get a second ``key:`` that silently replaces the first.
    """
    cfg = load_config(root)
    before: dict = getattr(cfg, key)
    config_file = cfg.config_path
    original = config_file.read_text(encoding="utf-8")
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
        updated = load_config(root)
        after: dict = getattr(updated, key)
        ok = applied(updated) and all(after.get(name) == value for name, value in before.items())
    except ConfigError:
        ok = False
    if not ok:
        config_file.write_text(original, encoding="utf-8")
        body = "\n".join(entry)
        raise ConfigError(f"could not add it to {config_file} automatically; add it by hand:\n{key}:\n{body}")


def add_capability_entry(root: Path, name: str, path: str, prefix: str = "", description: str = "") -> None:
    """Register a capability (name -> code path) in the config at ``root``, keeping the user's comments."""
    if not MODULE_NAME_RE.match(name):
        raise ConfigError(f"capability name '{name}' must be kebab-case (e.g. user-auth)")
    path = validate_relative(path, f"capability '{name}' path")
    if prefix and not PREFIX_RE.match(prefix):
        raise ConfigError(f"prefix '{prefix}' must be upper-case letters/digits (e.g. AUTH)")
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
