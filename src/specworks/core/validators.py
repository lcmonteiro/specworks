"""Validators for the names and paths a config holds: folders, module, capability and change names, ID prefixes, keys."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from .errors import ConfigError

DIR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")  # module, capability and change names
PREFIX_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*$")


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


def validate_kebab(name: object, what: str, example: str) -> str:
    """A module, capability or change name: ``what`` names it in the error (``capability name``)."""
    if not isinstance(name, str) or not KEBAB_RE.match(name):
        raise ConfigError(f"{what} '{name}' must be kebab-case (e.g. {example})")
    return name


def validate_module_name(name: object) -> str:
    return validate_kebab(name, "module name", "billing, user-service")


def validate_capability_name(name: object) -> str:
    return validate_kebab(name, "capability name", "user-auth")


def validate_prefix(prefix: str, where: str = "") -> str:
    """A requirement ID prefix (REQ-<prefix>-001); empty means derived from the capability name."""
    if prefix and not PREFIX_RE.match(prefix):
        raise ConfigError(f"{where}prefix '{prefix}' must be upper-case letters/digits (e.g. AUTH)")
    return prefix


def check_keys(raw: dict, allowed: tuple[str, ...], where: str) -> None:
    unknown = set(raw) - set(allowed)
    if unknown:
        raise ConfigError(f"{where} has unknown keys: {', '.join(sorted(map(str, unknown)))} (expected {', '.join(allowed)})")
