"""Shared CLI plumbing: options, JSON/text output, errors, and resolving the workspace and changes."""

from __future__ import annotations

import json
from typing import NoReturn

import typer

from ..core.changes import Change, ChangeError, ChangeFileError, list_changes, load_change
from ..core.config import CONFIG_EXT, DEFAULT_DIR, ConfigError, config_name
from ..core.workspace import Module, Workspace, load_workspace
from ..tools.skills import TOOLS

JsonOpt = typer.Option(False, "--json", help="Machine-readable output.")


ChangeOpt = typer.Option(..., "--change", "-c", help="Change name or module:name.")


AllOpt = typer.Option(False, "--all", help="Include every module of the workspace.")


ToolsOpt = typer.Option(
    "auto",
    "--tools",
    help=f"AI tools to install skills for: auto (detected; all if none), all, or a list of {', '.join(TOOLS)}.",
)


def emit(data: dict, as_json: bool, text: str) -> None:
    typer.echo(json.dumps(data, indent=2) if as_json else text)


def fail(message: str, as_json: bool, **extra) -> NoReturn:
    if as_json:
        typer.echo(json.dumps({"error": message, **extra}, indent=2))
    else:
        typer.echo(f"error: {message}", err=True)
    raise typer.Exit(1)


def workspace(as_json: bool) -> Workspace:
    try:
        ws = load_workspace()
    except ConfigError as exc:
        fail(str(exc), as_json)
    if ws is None:
        fail(
            f"no specworks config (<dir>{CONFIG_EXT}, e.g. {config_name(DEFAULT_DIR)}) found in this directory or its parents",
            as_json,
            root=None,
            fix="run `specworks init` at the repository root",
        )
    return ws


def change_dict(ws: Workspace, module: Module, change: Change) -> dict:
    return {
        "name": change.name,
        "ref": module.qualify(change.name),
        "module": module.label,
        "path": ws.rel(change.path),
        "phase": change.phase,
        "created": change.created,
        "skipSpecs": change.skip_specs,
    }


def module_dict(ws: Workspace, module: Module) -> dict:
    return {
        "name": module.label,
        "path": ws.rel(module.root),
        "dir": ws.rel(module.root / module.config.dir),
        "changesDir": ws.rel(module.config.changes_path),
        "current": module is ws.current,
    }


def missing_dicts(ws: Workspace) -> list[dict]:
    return [{"name": m.name, "path": ws.rel(m.path)} for m in ws.missing]


def changes_of(ws: Workspace, all_modules: bool) -> list[tuple[Module, Change]]:
    modules = ws.modules() if all_modules else [ws.current]
    return [(m, c) for m in modules for c in list_changes(m.config)]


def resolve_change(ws: Workspace, ref: str) -> tuple[Module, Change]:
    """``module:name`` is exact. A bare name prefers the current module, then any module if unique."""
    module, name = ws.split(ref)
    if module is not None:
        return module, load_change(module.config, name)
    # A broken .change.yaml is reported as such, not as "not found" (ChangeFileError is a ChangeError).
    try:
        return ws.current, load_change(ws.current.config, name)
    except ChangeFileError:
        raise
    except ChangeError:
        pass
    found = []
    for mod in ws.modules():
        try:
            found.append((mod, load_change(mod.config, name)))
        except ChangeFileError:
            raise
        except ChangeError:
            continue
    if len(found) == 1:
        return found[0]
    if found:
        refs = ", ".join(m.qualify(name) for m, _ in found)
        raise ChangeError(f"change '{name}' exists in several modules; use one of: {refs}")
    raise ChangeError(f"change '{name}' not found in any module")


def require_change(ref: str, as_json: bool) -> tuple[Workspace, Module, Change]:
    """The workspace and the change ``ref`` names, or exit with the error."""
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, ref)
    except (ChangeError, ConfigError) as exc:
        fail(str(exc), as_json)
    return ws, mod, ch
