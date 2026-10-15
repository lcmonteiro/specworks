"""Set-up and overview: init, skills, context, list, modules and capabilities."""

from __future__ import annotations

import re
from pathlib import Path

import typer

from .. import __version__
from ..core.config import DEFAULT_DIR, Config, ConfigError, config_name, find_config, load_config
from ..core.config_file import add_capability_entry, add_module_entry, write_default_config
from ..core.workspace import Workspace, load_module_config, load_workspace, require_workspace
from ..specs.capabilities import capability_ref, describe
from ..tools.skills import install_skills, parse_tools, remove_renamed_skills
from .app import app, capability_app, module_app
from .output import AllOpt, JsonOpt, ToolsOpt, change_dict, changes_of, emit, fail, missing_dicts, module_dict, workspace


def default_module_name(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.name.lower()).strip("-") or "module"


def write_skills(ws: Workspace, tools: str) -> None:
    """Install the skills at the workspace root (shared by every module)."""
    selected = parse_tools(tools, ws.root)
    typer.echo(f"tools   {', '.join(t.label for t in selected)}")
    for written in install_skills(ws.root, selected):
        typer.echo(f"skill   {ws.rel(written)}")
    for removed in remove_renamed_skills(ws.root, selected):
        typer.echo(f"removed {ws.rel(removed)} (renamed skill)")


def ensure_module_config(root: Path, name: str, workspace_dir: str) -> tuple[Config, bool]:
    """Load the module's <workspace_dir>.yml, creating it (and its changes folder) when missing.

    Fails before writing anything if the folder already has a config under another name.
    """
    existing = load_module_config(root, name, workspace_dir)
    if existing is None:
        root.mkdir(parents=True, exist_ok=True)
        write_default_config(root, workspace_dir)
    cfg = existing or load_config(root, workspace_dir)
    cfg.archive_path.mkdir(parents=True, exist_ok=True)
    return cfg, existing is None


def link_to_parent(root: Path, name: str | None) -> str | None:
    """Register ``root`` as a module of the nearest specworks project above it; return the name used."""
    parent = load_workspace(root.parent)
    if parent is None:
        return None
    owner = parent.current
    rel = root.relative_to(owner.root).as_posix()
    linked = next((n for n, p in owner.config.modules.items() if p == rel), None)
    if linked is None:
        linked = name or default_module_name(root)
        add_module_entry(owner.root, linked, rel)
    return f"{owner.name}/{linked}" if owner.name else linked  # nested modules are named parent/child


@app.command()
def version() -> None:
    """Print the specworks version."""
    typer.echo(__version__)


@app.command()
def init(
    path: Path = typer.Argument(Path("."), help="Project (or module) root."),
    dir: str | None = typer.Option(
        None, "--dir", help=f"Workflow folder name, also the config name: --dir spec -> spec.yml + spec/ (default: {DEFAULT_DIR})."
    ),
    name: str | None = typer.Option(None, "--name", help="Module name when linking to a parent project (default: folder name)."),
    diagram_theme: str | None = typer.Option(
        None, "--diagram-theme", help="Diagram theme for the workspace, by name or number (see `specworks diagrams --themes`)."
    ),
    no_link: bool = typer.Option(False, "--no-link", help="Do not register as a module of a parent specworks project."),
    tools: str = ToolsOpt,
    no_skills: bool = typer.Option(False, "--no-skills", help="Do not install agent skills."),
) -> None:
    """Create <dir>.yml and <dir>/changes/, link to a parent project, and install the agent skills."""
    root = path.resolve()
    parse_tools(tools, root)  # reject a bad --tools before writing anything
    parent = None if no_link else load_workspace(root.parent)
    if parent is not None:
        # A module shares the workspace's folder (and config file) name.
        workspace_dir = parent.top.config.dir
        if dir is not None and dir != workspace_dir:
            raise ConfigError(
                f"this folder is inside the workspace at {parent.root}, which uses {config_name(workspace_dir)}; "
                f"modules use the same name (drop --dir, or use --no-link for an independent project)"
            )
        cfg, created = ensure_module_config(root, name or default_module_name(root), workspace_dir)
    else:
        existing = find_config(root)
        if existing is None:
            root.mkdir(parents=True, exist_ok=True)
            write_default_config(root, DEFAULT_DIR if dir is None else dir, diagram_theme)
        elif dir is not None and existing.stem != dir:
            typer.echo(f"note    {existing.name} already exists; rename it (and its {existing.stem}/ folder) to change the name")
        cfg, created = load_config(root), existing is None
        cfg.archive_path.mkdir(parents=True, exist_ok=True)
    if created:
        typer.echo(f"created {cfg.config_path}")
    typer.echo(f"ready   {cfg.changes_path}/")
    if parent is not None:
        linked = link_to_parent(root, name)
        typer.echo(f"linked  as module '{linked}' of the parent project")
    ws = require_workspace(root)
    if not no_skills:
        write_skills(ws, tools)


@app.command()
def skills(tools: str = ToolsOpt) -> None:
    """Install or refresh the agent skills (e.g. after upgrading specworks)."""
    write_skills(workspace(False), tools)


@app.command()
def context(as_json: bool = JsonOpt, all_modules: bool = AllOpt) -> None:
    """Inherited context, all capabilities of the workspace, modules and changes."""
    ws = workspace(as_json)
    capabilities = []
    for mod, cap in ws.capabilities():
        docs = cap.docs_path(mod.root, mod.config.docs_dir)
        ref = capability_ref(mod, cap.name)
        capabilities.append(
            {
                "name": ref.ref,
                "module": mod.label,
                "path": ws.rel(mod.root / cap.path),
                "description": cap.description,
                "docsPath": ws.rel(docs),
                "hasSpec": (docs / "spec.md").is_file(),
                "prefix": ref.prefix,
                "deltaPath": ref.delta_path,
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
        "commands": ws.commands(),
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


@module_app.command("add")
def module_add(
    path: Path = typer.Argument(..., help="Folder of the module, relative to the current directory."),
    name: str | None = typer.Option(None, "--name", help="Module name (default: folder name)."),
    as_json: bool = JsonOpt,
) -> None:
    """Link a folder as a module of the current project, creating its config if needed.

    The module uses the workspace's config file and folder name (e.g. spec.yml and spec/).
    """
    ws = workspace(as_json)
    root = path.resolve()
    owner = ws.current
    if root == owner.root or not root.is_relative_to(owner.root):
        fail(f"{path} must be a folder inside {owner.root}", as_json)
    module_name = name or default_module_name(root)
    ensure_module_config(root, module_name, ws.top.config.dir)
    add_module_entry(owner.root, module_name, root.relative_to(owner.root).as_posix())
    ws = require_workspace(root)
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


@capability_app.command("add")
def capability_add(
    name: str = typer.Argument(..., help="Capability name (kebab-case)."),
    path: str = typer.Option(..., "--path", help="Code folder that owns it, relative to the module root."),
    module: str | None = typer.Option(None, "--module", "-m", help="Module that owns it (default: the current one)."),
    prefix: str = typer.Option("", "--prefix", help="Requirement ID prefix, e.g. AUTH (default: derived from the name)."),
    description: str = typer.Option("", "--description", help="One line on what it covers."),
    as_json: bool = JsonOpt,
) -> None:
    """Register a capability in a module's config (needed before closing a change that creates it)."""
    ws = workspace(as_json)
    target = ws.module(module) if module is not None else ws.current
    add_capability_entry(target.root, name, path, prefix=prefix, description=description)
    ws = require_workspace(target.root)
    data = describe(ws, capability_ref(ws.module(target.name), name), with_scenarios=False)
    emit(data, as_json, f"registered {data['ref']} -> {data['codePath']} (REQ-{data['prefix']}-)")
