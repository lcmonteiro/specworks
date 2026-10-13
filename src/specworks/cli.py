"""specworks command line interface.

Every command that agents read supports ``--json``. When no project is found the
JSON answer is ``{"root": null, ...}`` with exit code 1, so a skill can tell
"not set up" apart from a crash.

Paths in the output are relative to the workspace root (the top-level project),
which is printed as ``root``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import NoReturn

import typer

from . import __version__
from .changes import PHASES, Change, ChangeError, create_change, list_changes, load_change, set_phase
from .config import (
    CONFIG_FILE,
    DEFAULT_DIR,
    ConfigError,
    add_module_entry,
    default_config,
    load_config,
)
from .skills import install_skills
from .workflow import WorkflowError, artifact_states, instructions
from .workspace import Module, Workspace, load_workspace

app = typer.Typer(help="Spec-driven development: refine → propose → tests → code → review → verify → done.")
module_app = typer.Typer(help="Manage modules (sub-projects linked to this one, like git submodules).")
app.add_typer(module_app, name="module")

JsonOpt = typer.Option(False, "--json", help="Machine-readable output.")
AllOpt = typer.Option(False, "--all", help="Include every module of the workspace.")


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
            f"no {CONFIG_FILE} found in this directory or its parents",
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
    try:
        return ws.current, load_change(ws.current.config, name)
    except ChangeError:
        pass
    found = []
    for mod in ws.modules():
        try:
            found.append((mod, load_change(mod.config, name)))
        except ChangeError:
            continue
    if len(found) == 1:
        return found[0]
    if found:
        refs = ", ".join(m.qualify(name) for m, _ in found)
        raise ChangeError(f"change '{name}' exists in several modules; use one of: {refs}")
    raise ChangeError(f"change '{name}' not found in any module")


def default_module_name(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.name.lower()).strip("-") or "module"


def link_to_parent(root: Path, name: str | None) -> str | None:
    """Register ``root`` as a module of the nearest specworks project above it; return the name used."""
    parent = load_workspace(root.parent)
    if parent is None:
        return None
    owner = parent.current
    rel = root.relative_to(owner.root).as_posix()
    if rel in owner.config.modules.values():
        return next(n for n, p in owner.config.modules.items() if p == rel)
    module_name = name or default_module_name(root)
    add_module_entry(owner.root, module_name, rel)
    return owner.qualify(module_name) if owner.name else module_name


@app.command()
def version() -> None:
    """Print the specworks version."""
    typer.echo(__version__)


@app.command()
def init(
    path: Path = typer.Argument(Path("."), help="Project (or module) root."),
    dir: str | None = typer.Option(None, "--dir", help=f"Workflow folder, e.g. spec, docs, context (default: {DEFAULT_DIR})."),
    name: str | None = typer.Option(None, "--name", help="Module name when linking to a parent project (default: folder name)."),
    no_link: bool = typer.Option(False, "--no-link", help="Do not register as a module of a parent specworks project."),
    skills_dir: Path = typer.Option(Path(".claude/skills"), help="Where to install agent skills, relative to the workspace root."),
    no_skills: bool = typer.Option(False, "--no-skills", help="Do not install agent skills."),
) -> None:
    """Create specworks.yaml and the changes folder, link to a parent project, and install the agent skills."""
    root = path.resolve()
    root.mkdir(parents=True, exist_ok=True)
    config_file = root / CONFIG_FILE
    try:
        if not config_file.exists():
            config_file.write_text(default_config(DEFAULT_DIR if dir is None else dir), encoding="utf-8")
            typer.echo(f"created {config_file}")
        cfg = load_config(root)
        if dir is not None and cfg.dir != dir:
            typer.echo(f"note    {CONFIG_FILE} already exists with dir: {cfg.dir}; edit it to change the folder")
        cfg.archive_path.mkdir(parents=True, exist_ok=True)
        typer.echo(f"ready   {cfg.changes_path}/")
        if not no_link:
            linked = link_to_parent(root, name)
            if linked:
                typer.echo(f"linked  as module '{linked}' of the parent project")
        ws = load_workspace(root)
    except ConfigError as exc:
        fail(str(exc), False)
    if not no_skills:
        for written in install_skills(ws.root / skills_dir):
            typer.echo(f"skill   {ws.rel(written)}")


@app.command()
def context(as_json: bool = JsonOpt, all_modules: bool = AllOpt) -> None:
    """Inherited context, all capabilities of the workspace, modules and changes."""
    ws = workspace(as_json)
    capabilities = []
    for mod, cap in ws.capabilities():
        docs = cap.docs_path(mod.root, mod.config.docs_dir)
        capabilities.append(
            {
                "name": mod.qualify(cap.name),
                "module": mod.label,
                "path": ws.rel(mod.root / cap.path),
                "description": cap.description,
                "docsPath": ws.rel(docs),
                "hasSpec": (docs / "spec.md").is_file(),
            }
        )
    changes = changes_of(ws, all_modules)
    data = {
        "root": str(ws.root),
        "module": ws.current.label,
        "dir": ws.rel(ws.current.root / ws.current.config.dir),
        "changesDir": ws.rel(ws.current.config.changes_path),
        "context": ws.merged_context(),
        "contextChain": ws.context_chain(),
        "modules": [module_dict(ws, m) for m in ws.modules()],
        "missingModules": missing_dicts(ws),
        "capabilities": capabilities,
        "changes": [change_dict(ws, m, c) for m, c in changes],
    }
    lines = [f"root:    {ws.root}", f"module:  {ws.current.label}", "modules:"]
    lines += [f"  {m.label:<24} {ws.rel(m.root)}{'  *' if m is ws.current else ''}" for m in ws.modules()]
    lines += [f"  {m.name:<24} MISSING ({m.path})" for m in ws.missing]
    lines += ["capabilities:"] + ([f"  {c['name']:<24} {c['path']}" for c in capabilities] or ["  (none)"])
    lines += ["changes:"] + ([f"  {m.qualify(c.name):<24} {c.phase}" for m, c in changes] or ["  (none)"])
    emit(data, as_json, "\n".join(lines))


@app.command("list")
def list_cmd(as_json: bool = JsonOpt, all_modules: bool = AllOpt) -> None:
    """List active changes of the current module (or all modules with --all)."""
    ws = workspace(as_json)
    changes = changes_of(ws, all_modules)
    text = "\n".join(f"{m.qualify(c.name):<32} {c.phase}" for m, c in changes) or "no active changes"
    emit({"root": str(ws.root), "module": ws.current.label, "changes": [change_dict(ws, m, c) for m, c in changes]}, as_json, text)


@app.command()
def new(
    name: str,
    module: str | None = typer.Option(None, "--module", "-m", help="Create it in this module instead of the current one."),
    as_json: bool = JsonOpt,
) -> None:
    """Create a new change folder (phase: refine) in the current module."""
    ws = workspace(as_json)
    try:
        target = ws.module(module) if module is not None else ws.current
        change = create_change(target.config, name)
    except (ChangeError, ConfigError) as exc:
        fail(str(exc), as_json)
    emit(change_dict(ws, target, change), as_json, f"created {ws.rel(change.path)}")


@app.command()
def status(change: str = typer.Option(..., "--change", "-c", help="Change name or module:name."), as_json: bool = JsonOpt) -> None:
    """Phase and artifact states (done / ready / blocked) of a change."""
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
    except (ChangeError, ConfigError) as exc:
        fail(str(exc), as_json)
    states = artifact_states(ch)
    data = {**change_dict(ws, mod, ch), "phases": list(PHASES), "artifacts": states}
    text = "\n".join([f"{mod.qualify(ch.name)} (phase: {ch.phase})"] + [f"  [{s['status']:^7}] {s['generates']}" for s in states])
    emit(data, as_json, text)


@app.command()
def phase(
    name: str = typer.Argument(..., help="Change name or module:name."),
    to: str = typer.Argument(..., help=f"One of: {', '.join(PHASES)}"),
    as_json: bool = JsonOpt,
) -> None:
    """Move a change to another phase."""
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, name)
        set_phase(ch, to)
    except (ChangeError, ConfigError) as exc:
        fail(str(exc), as_json)
    emit(change_dict(ws, mod, ch), as_json, f"{mod.qualify(ch.name)}: phase → {ch.phase}")


@app.command("instructions")
def instructions_cmd(
    artifact: str,
    change: str = typer.Option(..., "--change", "-c", help="Change name or module:name."),
    as_json: bool = JsonOpt,
) -> None:
    """Template, rules and output path for writing one artifact of a change."""
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
        data = instructions(ws, mod, ch, artifact)
    except (ChangeError, ConfigError, WorkflowError) as exc:
        fail(str(exc), as_json)
    text = f"# {data['artifact']} → {data['outputPath']}\n\n{data['instruction']}\n---\n{data['template']}"
    emit(data, as_json, text)


@module_app.command("add")
def module_add(
    path: Path = typer.Argument(..., help="Folder of the module, relative to the current directory."),
    name: str | None = typer.Option(None, "--name", help="Module name (default: folder name)."),
    dir: str | None = typer.Option(None, "--dir", help="Workflow folder for a new module (default: same as the parent)."),
    as_json: bool = JsonOpt,
) -> None:
    """Link a folder as a module of the current project, creating its specworks.yaml if needed."""
    ws = workspace(as_json)
    root = path.resolve()
    owner = ws.current
    if root == owner.root or not root.is_relative_to(owner.root):
        fail(f"{path} must be a folder inside {owner.root}", as_json)
    try:
        root.mkdir(parents=True, exist_ok=True)
        if not (root / CONFIG_FILE).exists():
            (root / CONFIG_FILE).write_text(default_config(owner.config.dir if dir is None else dir), encoding="utf-8")
        cfg = load_config(root)
        cfg.archive_path.mkdir(parents=True, exist_ok=True)
        module_name = name or default_module_name(root)
        add_module_entry(owner.root, module_name, root.relative_to(owner.root).as_posix())
        ws = load_workspace(root)
    except ConfigError as exc:
        fail(str(exc), as_json)
    emit(module_dict(ws, ws.current), as_json, f"linked  {ws.rel(root)} as module '{ws.current.label}'")


@module_app.command("list")
def module_list(as_json: bool = JsonOpt) -> None:
    """List every module of the workspace (the current one is marked *)."""
    ws = workspace(as_json)
    data = {
        "root": str(ws.root),
        "modules": [module_dict(ws, m) for m in ws.modules()],
        "missingModules": missing_dicts(ws),
    }
    lines = [f"{m.label:<24} {ws.rel(m.root)}{'  *' if m is ws.current else ''}" for m in ws.modules()]
    lines += [f"{m.name:<24} MISSING ({m.path})" for m in ws.missing]
    emit(data, as_json, "\n".join(lines))


def main() -> None:
    app()
