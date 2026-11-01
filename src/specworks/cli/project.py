"""Set-up and overview: init, skills, context, list, modules and capabilities."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import typer

from .. import __version__
from ..core.changes import archived_as, list_archived
from ..core.config import Config, ConfigError, find_config, load_config, old_config_in, old_layout_error
from ..core.config_file import add_capability_entry, add_module_entry, save_tools, set_config_value, write_default_config
from ..core.git import require_repo
from ..core.validators import validate_relative
from ..core.workspace import Module, Workspace, capability_prefix, load_module_config, load_workspace, require_workspace
from ..specs.capabilities import capability_ref, describe
from ..tools.skills import TOOLS, Tool, install_skills, parse_tools, remove_stale_skills, resolve_tools, skills_state, update_skills
from .app import app, capability_app, config_app, module_app
from .output import AllOpt, JsonOpt, ToolsOpt, change_dict, changes_of, emit, fail, missing_dicts, module_dict, workspace


def default_module_name(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.name.lower()).strip("-") or "module"


# @req REQ-CLI-003
def is_terminal() -> bool:
    """Whether init runs in a terminal and may ask which tools the project uses (replaced in tests)."""
    return sys.stdin.isatty()


# @req REQ-CLI-003
def ask_tools(root: Path) -> str:
    """Ask which AI tools the project uses, the detected ones as the default; checked like ``--tools``."""
    detected = ",".join(t.id for t in parse_tools("auto", root))
    answer = typer.prompt(f"AI tools to install skills for ({', '.join(TOOLS)})", default=detected)
    parse_tools(answer, root)  # an unknown or empty answer fails before anything is written
    return answer


# @req REQ-INTEG-004, REQ-CLI-003, REQ-CLI-009
def chosen_tools(ws: Workspace, given: str | None) -> list[Tool]:
    """The tools to install for (``--tools``, else the saved choice, else the inferred one), saved in the top level's config when asked."""
    saved = ws.top.config.tools
    selected, save = resolve_tools(ws.root, saved, given)
    ids = [t.id for t in selected]
    if save and ids != saved:
        save_tools(ws.root, ids)
        typer.echo(f"saved   tools: [{', '.join(ids)}] in {ws.rel(ws.top.config.config_path)}")
    typer.echo(f"tools   {', '.join(t.label for t in selected)}")
    return selected


def write_skills(ws: Workspace, tools: str | None) -> None:
    """Install the skills at the workspace root (shared by every module)."""
    selected = chosen_tools(ws, tools)
    for removed in remove_stale_skills(ws.root, selected):  # renamed or dropped by this version  @req REQ-INTEG-005
        typer.echo(f"removed {ws.rel(removed)}")
    for written in install_skills(ws.root, selected):
        typer.echo(f"skill   {ws.rel(written)}")


def ensure_module_config(root: Path, name: str) -> tuple[Config, bool]:
    """Load the module's .specworks/config.yml, creating it (and its changes folder) when missing.

    Fails before writing anything if the folder still has the old layout.
    """
    existing = load_module_config(root, name)
    if existing is None:
        write_default_config(root)
    cfg = existing or load_config(root)
    make_change_dirs(cfg)
    return cfg, existing is None


def make_change_dirs(cfg: Config) -> None:
    cfg.changes_path.mkdir(parents=True, exist_ok=True)
    cfg.archive_path.mkdir(parents=True, exist_ok=True)


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


def held_module(ws: Workspace, root: Path) -> Module | None:
    """A module of ``ws`` inside the folder ``root``, unless ``root`` is a module itself.

    Linking such a folder would leave that module listed past it, which loading refuses.
    """
    inner = [m for m in ws.modules() if m.root.is_relative_to(root)]
    return inner[0] if inner and all(m.root != root for m in inner) else None


def held_message(ws: Workspace, path: Path, inner: Module) -> str:
    return f"{path} holds module '{inner.label}' ({ws.rel(inner.root)}); a module can't be added around another one"


def module_lines(ws: Workspace, indent: str = "") -> list[str]:
    """One line per module (the current one marked *), then the missing ones."""
    lines = [f"{indent}{m.label:<24} {ws.rel(m.root)}{'  *' if m is ws.current else ''}" for m in ws.modules()]
    return lines + [f"{indent}{m.name:<24} MISSING ({m.path})" for m in ws.missing]


@app.command()
def version() -> None:
    """Print the specworks version."""
    typer.echo(__version__)


# @req REQ-CLI-003
@app.command()
def init(
    path: Path = typer.Argument(Path("."), help="Project (or module) root."),
    name: str | None = typer.Option(None, "--name", help="Module name when linking to a parent project (default: folder name)."),
    diagram_theme: str | None = typer.Option(
        None, "--diagram-theme", help="Diagram theme for the workspace, by name or number (see `specworks diagrams --themes`)."
    ),
    no_link: bool = typer.Option(False, "--no-link", help="Do not register as a module of a parent specworks project."),
    tools: str | None = ToolsOpt,
    no_skills: bool = typer.Option(False, "--no-skills", help="Do not install agent skills."),
) -> None:
    """Create .specworks/config.yml and .specworks/changes/active/ and archive/, link to a parent project, and install the agent skills."""
    root = path.resolve()
    if tools is not None:
        parse_tools(tools, root)  # reject a bad --tools before writing anything
    require_repo(root)
    parent = None if no_link else load_workspace(root.parent)
    # A new top level, or one that saves no tools yet: ask in a terminal, before anything is written.
    if not no_skills and tools is None and parent is None and is_terminal():
        existing = find_config(root)
        if (existing is None and old_config_in(root) is None) or (existing is not None and load_config(root).tools is None):
            tools = ask_tools(root)
    if parent is not None:
        if inner := held_module(parent, root):
            raise ConfigError(held_message(parent, path, inner))
        cfg, created = ensure_module_config(root, name or default_module_name(root))
    else:
        existing = find_config(root)
        if existing is None and (old := old_config_in(root)) is not None:  # never a second, empty project beside an old one  @req REQ-PROJ-021
            raise old_layout_error(old)
        if existing is None:
            write_default_config(root, diagram_theme)
        cfg, created = load_config(root), existing is None
        make_change_dirs(cfg)
    linked = link_to_parent(root, name) if parent is not None else None
    ws = require_workspace(root)
    # Paths relative to the workspace root, like every other command's output.
    if diagram_theme is not None and (parent is not None or not created):
        typer.echo(f"note    --diagram-theme not applied: set diagrams.theme in {ws.rel(ws.top.config.config_path)} (the top level's diagrams apply everywhere)")
    if created:
        typer.echo(f"created {ws.rel(cfg.config_path)}")
    typer.echo(f"ready   {ws.rel(cfg.changes_path)}/")
    if linked is not None:
        typer.echo(f"linked  as module '{linked}' of the parent project")
    if not no_skills:
        write_skills(ws, tools)


@app.command()
def skills(tools: str | None = ToolsOpt) -> None:
    """Install or refresh the agent skills (e.g. after upgrading specworks)."""
    write_skills(workspace(False), tools)


# @req REQ-CLI-009
@app.command()
def update(
    tools: str | None = ToolsOpt,
) -> None:
    """Bring the project's agent skills up to this specworks (run after `uv tool upgrade specworks`)."""
    ws = workspace(False)
    selected = chosen_tools(ws, tools)
    updated, removed = update_skills(ws.root, selected)
    for path in removed:
        typer.echo(f"removed {ws.rel(path)}")
    for path in updated:
        typer.echo(f"updated {ws.rel(path)}")
    if not updated and not removed:
        typer.echo("skills up to date")


# @req REQ-CLI-004
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
    skills = skills_state(ws.root, ws.top.config.tools)
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
        "skills": {"state": skills.state, "files": [{"path": f.path, "reason": f.reason} for f in skills.files]},
    }
    lines = [f"root:    {ws.root}", f"module:  {ws.current.label}", "modules:", *module_lines(ws, "  ")]
    lines += ["capabilities:"] + ([f"  {c['name']:<24} {c['path']}" for c in capabilities] or ["  (none)"])
    lines += ["changes:"] + ([f"  {m.qualify(c.name):<24} {c.phase}" for m, c in changes] or ["  (none)"])
    if skills.state == "outdated":
        lines += [f"skills:  outdated ({len(skills.files)} files)", "skills out of date: run specworks update"]
    else:
        lines += [f"skills:  {skills.state}"]
    emit(data, as_json, "\n".join(lines))


# @req REQ-CLI-004
@app.command("list")
def list_cmd(
    as_json: bool = JsonOpt,
    all_modules: bool = AllOpt,
    archived: bool = typer.Option(False, "--archived", help="List closed and abandoned changes instead of active ones."),
) -> None:
    """List active changes of the current module (or all modules with --all)."""
    ws = workspace(as_json)
    modules = ws.modules() if all_modules else [ws.current]
    rows, lines = [], []
    if archived:
        for m in modules:
            for c in list_archived(m.config):
                rows.append(change_dict(ws, m, c))
                state = f"abandoned in {c.phase}: {c.abandoned}" if c.abandoned else "closed"
                lines.append(f"{m.qualify(c.name):<32} {c.path.name[:10]}  {state}")
    else:
        for m, c in changes_of(ws, all_modules):
            row = change_dict(ws, m, c)
            line = f"{m.qualify(c.name):<32} {c.phase}"
            if twin := archived_as(m.config, c.name):
                row["alsoArchived"] = ws.rel(twin.path)
                line += f"  (also archived at {row['alsoArchived']}: a leftover copy?)"
            rows.append(row)
            lines.append(line)
    empty = "no archived changes" if archived else "no active changes"
    emit({"root": str(ws.root), "module": ws.current.label, "changes": rows}, as_json, "\n".join(lines) or empty)


# @req REQ-CLI-005
@module_app.command("add")
def module_add(
    path: Path = typer.Argument(..., help="Folder of the module, relative to the current directory."),
    name: str | None = typer.Option(None, "--name", help="Module name (default: folder name)."),
    as_json: bool = JsonOpt,
) -> None:
    """Link a folder as a module of the innermost module holding it, creating its config if needed.

    The module gets its own .specworks/config.yml, like every project.
    """
    ws = workspace(as_json)
    root = path.resolve()
    owner = ws.current
    if root == owner.root or not root.is_relative_to(owner.root):
        fail(f"{path} must be a folder inside {owner.root}", as_json)
    owner = ws.owner(root.parent)  # the innermost module holding the folder lists it, as with init
    if inner := held_module(ws, root):
        fail(held_message(ws, path, inner), as_json)
    module_name = name or default_module_name(root)
    ensure_module_config(root, module_name)
    add_module_entry(owner.root, module_name, root.relative_to(owner.root).as_posix())
    ws = require_workspace(root)
    emit(module_dict(ws, ws.current), as_json, f"linked  {ws.rel(root)} as module '{ws.current.label}'")


# @req REQ-CLI-004
@module_app.command("list")
def module_list(as_json: bool = JsonOpt) -> None:
    """List every module of the workspace (the current one is marked *)."""
    ws = workspace(as_json)
    data = {
        "root": str(ws.root),
        "modules": [module_dict(ws, m) for m in ws.modules()],
        "missingModules": missing_dicts(ws),
    }
    emit(data, as_json, "\n".join(module_lines(ws)))


# @req REQ-CLI-005
@capability_app.command("add")
def capability_add(
    name: str = typer.Argument(..., help="Capability name (kebab-case)."),
    path: str = typer.Option(..., "--path", help="Code folder that owns it, relative to the module root."),
    module: str | None = typer.Option(None, "--module", "-m", help="Module that owns it (default: the current one)."),
    prefix: str = typer.Option("", "--prefix", help="Requirement ID prefix, e.g. AUTH (default: derived from the name)."),
    description: str = typer.Option("", "--description", help="One line on what it covers."),
    create: bool = typer.Option(False, "--create", help="Create the code folder with an empty .gitkeep when it does not exist."),
    as_json: bool = JsonOpt,
) -> None:
    """Register a capability in a module's config (needed before closing a change that creates it).

    With --create, also create its code folder with an empty .gitkeep. Implements REQ-CLI-014.
    """
    ws = workspace(as_json)
    target = ws.module(module) if module is not None else ws.current
    id_prefix = capability_prefix(target.name, name, prefix)
    owner = ws.prefixes().get(id_prefix)
    if owner and owner != target.qualify(name):  # the same name is reported as "already exists" below
        raise ConfigError(f"the ID prefix {id_prefix} is already used by {owner}; choose another with --prefix")
    folder = ws.docs_folder(target, validate_relative(path, f"capability '{name}' path"))  # as the config will store it
    if (taken := ws.docs_folders().get(folder)) and taken != target.qualify(name):  # @req REQ-PROJ-016
        where = ws.rel(folder) if folder.is_relative_to(ws.root) else folder.as_posix()
        raise ConfigError(f"the docs folder {where} is already used by {taken}; give {name} its own --path")
    add_capability_entry(target.root, name, path, prefix=prefix, description=description)
    ws = require_workspace(target.root)
    data = describe(ws, capability_ref(ws.module(target.name), name), with_scenarios=False)
    data["created"] = None  # stub: --create is accepted but creates nothing yet; this becomes the .gitkeep path relative to the workspace root
    emit(data, as_json, f"registered {data['ref']} -> {data['codePath']} (REQ-{data['prefix']}-)")


# @req REQ-CLI-013
@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="context, or commands.<test|lint|typecheck|build|format>."),
    value: str | None = typer.Argument(None, help="The value (empty clears the key); or use --file."),
    file: str | None = typer.Option(None, "--file", help="Read the value from this file (- for standard input)."),
    module: str | None = typer.Option(None, "--module", "-m", help="Module whose config to set (default: the current one)."),
    as_json: bool = JsonOpt,
) -> None:
    """Set a command or the context in a module's config, keeping its comments. Implements REQ-CLI-013."""
    if value is not None and file is not None:
        fail("give the value as an argument or with --file, not both", as_json)
    if value is None and file is None:
        fail("give a value, or --file <path> (- for standard input)", as_json)
    ws = workspace(as_json)
    target = ws.module(module) if module is not None else ws.current
    if file is None:
        text = value or ""
    else:
        try:
            raw = sys.stdin.read() if file == "-" else Path(file).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            fail(f"cannot read {file}: {exc}", as_json)
        text = raw.rstrip("\r\n")  # the newline that ends a file or an echo is not part of the value
    set_config_value(target.root, key, text)
    config = ws.rel(target.config.config_path)
    emit({"key": key, "value": text, "config": config, "module": target.label}, as_json, f"set {key} in {config}")
