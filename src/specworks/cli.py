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
    add_capability_entry,
    DARK_THEMES,
    THEMES,
    theme_name,
    CONFIG_EXT,
    DEFAULT_DIR,
    Config,
    ConfigError,
    add_module_entry,
    config_name,
    find_config,
    load_config,
    write_default_config,
)
from .skills import TOOLS, ToolError, install_skills, parse_tools, remove_renamed_skills
from .diagrams import DiagramError, diagrams_in, find_d2, render, state
from .gate import GATES, GateError, run_gate
from .review import review_change
from .runner import CommandError, run_command
from .specs import capability_ref, describe, resolve_ref, workspace_capabilities
from .tasks import TaskError, read_tasks, set_done
from .trace import build_matrix, gaps, scan_tags, to_markdown, unknown_tags, write_traceability
from .validate import validate_change
from .workflow import WorkflowError, artifact_states, instructions
from .workspace import Module, Workspace, load_module_config, load_workspace

app = typer.Typer(help="Spec-driven development: refine → specify → design → test → code → review → validate → close.")
module_app = typer.Typer(help="Manage modules (sub-projects linked to this one, like git submodules).")
app.add_typer(module_app, name="module")
spec_app = typer.Typer(help="Read capabilities and their living specs.")
app.add_typer(spec_app, name="spec")
task_app = typer.Typer(help="List and tick the tasks of a change (tasks.md).")
app.add_typer(task_app, name="task")
capability_app = typer.Typer(help="Register capabilities (durable behaviours owned by a code folder).")
app.add_typer(capability_app, name="capability")

JsonOpt = typer.Option(False, "--json", help="Machine-readable output.")
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


def write_skills(ws: Workspace, tools: str) -> None:
    """Install the skills at the workspace root (shared by every module)."""
    try:
        selected = parse_tools(tools, ws.root)
    except ToolError as exc:
        fail(str(exc), False)
    typer.echo(f"tools   {', '.join(t.label for t in selected)}")
    for written in install_skills(ws.root, selected):
        typer.echo(f"skill   {ws.rel(written)}")
    for removed in remove_renamed_skills(ws.root, selected):
        typer.echo(f"removed {ws.rel(removed)} (renamed skill)")


def ensure_module_config(root: Path, name: str, workspace_dir: str) -> tuple[Config, bool]:
    """Load the module's <workspace_dir>.yml, creating it (and its changes folder) when missing.

    Fails before writing anything if the folder already has a config under another name.
    """
    cfg = load_module_config(root, name, workspace_dir)
    created = cfg is None
    if created:
        root.mkdir(parents=True, exist_ok=True)
        write_default_config(root, workspace_dir)
        cfg = load_config(root, workspace_dir)
    cfg.archive_path.mkdir(parents=True, exist_ok=True)
    return cfg, created


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
    try:
        parse_tools(tools, root)  # reject a bad --tools before writing anything
    except ToolError as exc:
        fail(str(exc), False)
    try:
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
        ws = load_workspace(root)
    except ConfigError as exc:
        fail(str(exc), False)
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


@app.command("check")
def check_cmd(
    change: str = typer.Option(..., "--change", "-c", help="Change name or module:name."),
    strict: bool = typer.Option(False, "--strict", help="Treat warnings as errors."),
    as_json: bool = JsonOpt,
) -> None:
    """Check a change's proposal, delta specs and tasks (IDs, SHALL/MUST, scenarios, coverage)."""
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
    except (ChangeError, ConfigError) as exc:
        fail(str(exc), as_json)
    _, issues = validate_change(ws, ch)
    errors = [i for i in issues if i.level == "error" or strict]
    data = {
        **change_dict(ws, mod, ch),
        "valid": not errors,
        "errors": sum(i.level == "error" for i in issues),
        "warnings": sum(i.level == "warning" for i in issues),
        "issues": [i.to_dict() for i in issues],
    }
    verdict = "valid" if not errors else "INVALID"
    text = "\n".join([*(str(i) for i in issues), f"{mod.qualify(ch.name)}: {verdict} ({data['errors']} errors, {data['warnings']} warnings)"])
    emit(data, as_json, text)
    if errors:
        raise typer.Exit(1)


@app.command()
def trace(
    change: str = typer.Option(..., "--change", "-c", help="Change name or module:name."),
    write: bool = typer.Option(False, "--write", help="Write traceability.md in the change folder."),
    as_json: bool = JsonOpt,
) -> None:
    """Requirement -> acceptance criterion -> task -> test (@ac) -> code (@req) matrix of a change."""
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
    except (ChangeError, ConfigError) as exc:
        fail(str(exc), as_json)
    specs, issues = validate_change(ws, ch)
    tags = scan_tags(ws)
    rows = build_matrix(specs, tags)
    found = gaps(rows)
    markdown = to_markdown(mod.qualify(ch.name), rows, found)
    written = ws.rel(write_traceability(ch, markdown)) if write else None
    data = {
        **change_dict(ws, mod, ch),
        "rows": [vars(r) for r in rows],
        "gaps": found,
        "unknownTags": [{"id": t.id, "where": t.where} for t in unknown_tags(specs, tags)],
        "specErrors": sum(i.level == "error" for i in issues),
        "written": written,
    }
    text = markdown + (f"\nwrote {written}" if written else "")
    emit(data, as_json, text)


@app.command()
def diagrams(
    change: str | None = typer.Option(None, "--change", "-c", help="Change name or module:name."),
    themes: bool = typer.Option(False, "--themes", help="List the diagram themes and the one in use."),
    check: bool = typer.Option(False, "--check", help="Only report missing or outdated SVGs (exit 1 if any); no d2 needed."),
    force: bool = typer.Option(False, "--force", help="Re-render every diagram, even up-to-date ones."),
    dir: Path | None = typer.Option(None, "--dir", help="Render <dir>/diagrams/*.d2 instead (e.g. a capability's living docs folder)."),
    as_json: bool = JsonOpt,
) -> None:
    """Render D2 diagrams (diagrams/*.d2) of a change, or of a docs folder, to SVG with the workspace's settings."""
    ws = workspace(as_json)
    settings = ws.top.config.diagrams
    if themes:
        rows = [{"name": n, "id": i, "dark": n in DARK_THEMES} for n, i in THEMES.items()]
        d2_path, d2_from = find_d2()
        data = {
            "theme": theme_name(settings.theme),
            "darkTheme": theme_name(settings.dark_theme),
            "d2": d2_path,
            "d2From": d2_from,
            "themes": rows,
        }
        lines = [
            f"in use: theme {data['theme']}, dark_theme {data['darkTheme']}  ({ws.rel(ws.top.config.config_path)})",
            f"d2:     {d2_path or 'not found'} ({d2_from})",
        ]
        lines += [f"  {r['id']:>4}  {r['name']}{'  (dark)' if r['dark'] else ''}" for r in rows]
        emit(data, as_json, "\n".join(lines))
        return
    if (change is None) == (dir is None):
        fail("give either --change <ref> or --dir <folder> (or --themes)", as_json)
    if dir is not None:
        folder = dir.resolve()
        if not folder.is_relative_to(ws.root):
            fail(f"{dir} is outside the workspace", as_json)
        header = {"root": str(ws.root), "dir": ws.rel(folder)}
    else:
        try:
            mod, ch = resolve_change(ws, change)
        except (ChangeError, ConfigError) as exc:
            fail(str(exc), as_json)
        folder, header = ch.path, change_dict(ws, mod, ch)
    results, failed = [], False
    for diagram in diagrams_in(folder):
        status = state(diagram, settings)
        entry = {"source": ws.rel(diagram.source), "svg": ws.rel(diagram.svg), "status": status}
        if not check and (force or status != "ok"):
            try:
                render(diagram, settings)
                entry["status"] = "rendered"
            except DiagramError as exc:
                entry.update(status="error", error=str(exc))
        failed |= entry["status"] in ("missing", "stale", "error")
        results.append(entry)
    d2_path, d2_from = find_d2()
    data = {**header, "d2": d2_path, "d2From": d2_from, "diagrams": results}
    lines = [f"{r['status']:<9} {r['svg']}" + (f"\n          {r['error']}" if "error" in r else "") for r in results]
    emit(data, as_json, "\n".join(lines) or "no diagrams (add diagrams/<name>.d2)")
    if failed:
        raise typer.Exit(1)


@app.command()
def gate(
    phase: str = typer.Argument(..., help=f"Phase to check: {', '.join(GATES)}."),
    change: str = typer.Option(..., "--change", "-c", help="Change name or module:name."),
    no_run: bool = typer.Option(False, "--no-run", help="design/code/review: do not run the project's commands (reported as a warning)."),
    base: str | None = typer.Option(None, "--base", help="review: branch to diff against (default: origin's default branch)."),
    as_json: bool = JsonOpt,
) -> None:
    """Check whether a change has finished a phase (exit 1 if a blocking check fails)."""
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
        passed, checks = run_gate(ws, mod, ch, phase, run_tests=not no_run, base=base)
    except (ChangeError, ConfigError, GateError) as exc:
        fail(str(exc), as_json)
    data = {**change_dict(ws, mod, ch), "gate": phase, "passed": passed, "checks": [c.to_dict() for c in checks]}
    lines = []
    for c in checks:
        mark = "ok  " if c.ok else ("FAIL" if c.blocking else "warn")
        lines.append(f"[{mark}] {c.name}")
        lines += [f"         {d}" for d in c.details]
    lines.append(f"gate {phase}: {'passed' if passed else 'NOT passed'}")
    emit(data, as_json, "\n".join(lines))
    if not passed:
        raise typer.Exit(1)


@app.command()
def close(
    change: str = typer.Option(..., "--change", "-c", help="Change name or module:name."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be merged and archived; write nothing."),
    base: str | None = typer.Option(None, "--base", help="Branch to diff against for validate (default: origin's default branch)."),
    no_run: bool = typer.Option(False, "--no-run", help="Validate without running test/lint/typecheck."),
    as_json: bool = JsonOpt,
) -> None:
    """Merge the change's delta specs into the living specs, update requirements.md, and archive the change."""
    from .merge import MergeError, archive_change, plan_merge, write_merge
    from .validate import validate_change
    from .verify import summary, verify_change

    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
    except (ChangeError, ConfigError) as exc:
        fail(str(exc), as_json)
    ref = mod.qualify(ch.name)
    result = summary(verify_change(ws, mod, ch, run=not no_run, base=base))
    if result["verdict"] != "PASS":
        fail(
            f"{ref} does not pass validate ({result['critical']} critical); run `specworks validate --change {ref}`",
            as_json,
            goBackTo=result["goBackTo"],
        )
    specs, _ = validate_change(ws, ch)
    try:
        merges = plan_merge(ws, ch, specs, ref)
    except MergeError as exc:
        fail(str(exc), as_json)
    data = {**change_dict(ws, mod, ch), "dryRun": dry_run, "merges": [m.to_dict(ws) for m in merges], "archivedTo": None}
    lines = [f"{'would merge' if dry_run else 'merged'} {m.cap.ref} -> {ws.rel(m.spec_path)}{' (new)' if m.created else ''}: {m.summary()}" for m in merges]
    lines = lines or ["no delta specs to merge (skip_specs)"]
    if not dry_run:
        try:
            write_merge(merges)
            target = archive_change(ch, mod.config.archive_path)
        except (MergeError, OSError) as exc:
            fail(str(exc), as_json)
        data["archivedTo"] = ws.rel(target)
        data["phase"] = "done"
        lines.append(f"archived -> {data['archivedTo']}")
    emit(data, as_json, "\n".join(lines))


@app.command("validate")
def validate_cmd(
    change: str = typer.Option(..., "--change", "-c", help="Change name or module:name."),
    base: str | None = typer.Option(None, "--base", help="Branch to diff against (default: origin's default branch)."),
    no_run: bool = typer.Option(False, "--no-run", help="Do not run test/lint/typecheck (reported as warnings)."),
    as_json: bool = JsonOpt,
) -> None:
    """Final read-only check before close (validate phase): completeness, correctness, coherence (exit 1 on FAIL)."""
    from .verify import GROUPS, summary, verify_change

    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
    except (ChangeError, ConfigError) as exc:
        fail(str(exc), as_json)
    checks = verify_change(ws, mod, ch, run=not no_run, base=base)
    result = summary(checks)
    data = {**change_dict(ws, mod, ch), **result, "checks": [c.to_dict() for c in checks]}
    lines = []
    for group in GROUPS:
        counts = result["groups"][group]
        lines.append(f"{group.capitalize()} ({counts['passed']}/{counts['total']})")
        for c in (c for c in checks if c.group == group):
            mark = "ok  " if c.ok else ("FAIL" if c.blocking else "warn")
            lines.append(f"  [{mark}] {c.name}" + ("" if c.ok else f"  -> {c.fix}"))
            lines += [f"           {d}" for d in c.details if not c.ok or d.startswith("$ ")]
    lines.append(f"{mod.qualify(ch.name)}: {result['verdict']} ({result['critical']} critical, {result['warnings']} warnings)")
    if result["goBackTo"]:
        lines.append(f"go back to: {', '.join(result['goBackTo'])}")
    emit(data, as_json, "\n".join(lines))
    if result["verdict"] != "PASS":
        raise typer.Exit(1)


@app.command()
def review(
    change: str = typer.Option(..., "--change", "-c", help="Change name or module:name."),
    base: str | None = typer.Option(None, "--base", help="Branch to diff against (default: origin's default branch)."),
    as_json: bool = JsonOpt,
) -> None:
    """Drift candidates between a change's specs and its code, in both directions."""
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
    except (ChangeError, ConfigError) as exc:
        fail(str(exc), as_json)
    _, report = review_change(ws, ch, base)
    data = {**change_dict(ws, mod, ch), **report.to_dict()}
    labels = {
        "reqWithoutCode": "requirements without code (@req)",
        "acWithoutTests": "acceptance criteria without tests (@ac)",
        "removedStillTagged": "removed requirements still tagged",
        "unknownTags": "tags to unknown IDs",
        "untracedSource": "changed code files without @req tags",
        "untracedTests": "changed test files without @ac tags",
    }
    lines = [f"base: {report.base or '-'}"] + ([f"note: {report.note}"] if report.note else [])
    lines += [f"spec error: {e}" for e in report.spec_errors]
    for key, items in data["findings"].items():
        lines.append(f"{labels[key]}: {len(items)}")
        lines += [f"  {item}" for item in items]
    lines.append(f"{data['findingCount']} drift candidates")
    emit(data, as_json, "\n".join(lines))


@app.command()
def run(
    key: str = typer.Argument(..., help="Command to run: test, lint, typecheck, build or format."),
    change: str | None = typer.Option(None, "--change", "-c", help="Run in the module owning this change."),
    as_json: bool = JsonOpt,
) -> None:
    """Run one of the project's configured commands in the right module folder (exit code passes through)."""
    ws = workspace(as_json)
    try:
        mod = resolve_change(ws, change)[0] if change else ws.current
        result = run_command(ws, mod, key, capture=as_json)
    except (ChangeError, ConfigError, CommandError) as exc:
        fail(str(exc), as_json)
    if as_json:
        typer.echo(
            json.dumps(
                {"key": key, "command": result.command, "cwd": result.cwd, "exitCode": result.exit_code, "ok": result.ok, "tail": result.tail()},
                indent=2,
            )
        )
    raise typer.Exit(result.exit_code)


def _task_change(as_json: bool, change: str):
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
    except (ChangeError, ConfigError) as exc:
        fail(str(exc), as_json)
    return ws, mod, ch


def _emit_tasks(ws, mod, ch, tasks, as_json: bool) -> None:
    done = sum(t.done for t in tasks)
    data = {**change_dict(ws, mod, ch), "done": done, "total": len(tasks), "tasks": [t.to_dict() for t in tasks]}
    lines = [f"[{'x' if t.done else ' '}] {t.num} {t.text}" for t in tasks] + [f"{done}/{len(tasks)} done"]
    emit(data, as_json, "\n".join(lines))


@task_app.command("list")
def task_list(
    change: str = typer.Option(..., "--change", "-c", help="Change name or module:name."),
    pending: bool = typer.Option(False, "--pending", help="Only tasks not done yet."),
    as_json: bool = JsonOpt,
) -> None:
    """List the tasks of a change with their IDs and state."""
    ws, mod, ch = _task_change(as_json, change)
    try:
        tasks = read_tasks(ch.path)
    except TaskError as exc:
        fail(str(exc), as_json)
    _emit_tasks(ws, mod, ch, [t for t in tasks if not (pending and t.done)], as_json)


def _set(change: str, nums: list[str], done: bool, as_json: bool) -> None:
    ws, mod, ch = _task_change(as_json, change)
    try:
        set_done(ch.path, nums, done)
        tasks = read_tasks(ch.path)
    except TaskError as exc:
        fail(str(exc), as_json)
    _emit_tasks(ws, mod, ch, tasks, as_json)


@task_app.command("done")
def task_done(
    nums: list[str] = typer.Argument(..., help="Task numbers, e.g. 1.1 1.2."),
    change: str = typer.Option(..., "--change", "-c", help="Change name or module:name."),
    as_json: bool = JsonOpt,
) -> None:
    """Tick tasks as done (- [x])."""
    _set(change, nums, True, as_json)


@task_app.command("undo")
def task_undo(
    nums: list[str] = typer.Argument(..., help="Task numbers, e.g. 1.1 1.2."),
    change: str = typer.Option(..., "--change", "-c", help="Change name or module:name."),
    as_json: bool = JsonOpt,
) -> None:
    """Mark tasks as not done (- [ ])."""
    _set(change, nums, False, as_json)


@spec_app.command("show")
def spec_show(
    ref: str = typer.Argument(..., help="Capability name, or module:name for another module."),
    no_scenarios: bool = typer.Option(False, "--no-scenarios", help="Only requirement IDs and titles."),
    as_json: bool = JsonOpt,
) -> None:
    """A capability's living spec, ID prefix, next free ID and delta path (also for a new capability)."""
    ws = workspace(as_json)
    try:
        cap = resolve_ref(ws, ref)
    except ConfigError as exc:
        fail(str(exc), as_json)
    data = describe(ws, cap, with_scenarios=not no_scenarios)
    lines = [
        f"{data['ref']}{'  (new)' if data['new'] else ''}",
        f"  prefix:    REQ-{data['prefix']}-  next: {data['nextId']}",
        f"  delta:     {data['deltaPath']}",
        f"  living:    {data['livingSpec'] or '-'}",
    ]
    lines += [f"  {r['id']}  {r['title']}" for r in data["requirements"]]
    emit(data, as_json, "\n".join(lines))


@spec_app.command("list")
def spec_list(as_json: bool = JsonOpt) -> None:
    """Every capability of the workspace with its prefix and living spec."""
    ws = workspace(as_json)
    caps = [describe(ws, c, with_scenarios=False) for c in workspace_capabilities(ws)]
    for c in caps:
        c["requirements"] = len(c["requirements"])
    text = "\n".join(f"{c['ref']:<28} REQ-{c['prefix']}-  {c['requirements']} req  {c['livingSpec']}" for c in caps)
    emit({"root": str(ws.root), "capabilities": caps}, as_json, text or "no capabilities")


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
    try:
        target = ws.module(module) if module is not None else ws.current
        add_capability_entry(target.root, name, path, prefix=prefix, description=description)
        ws = load_workspace(target.root)
        data = describe(ws, capability_ref(ws.module(target.name), name), with_scenarios=False)
    except ConfigError as exc:
        fail(str(exc), as_json)
    emit(data, as_json, f"registered {data['ref']} -> {data['codePath']} (REQ-{data['prefix']}-)")


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
    try:
        module_name = name or default_module_name(root)
        ensure_module_config(root, module_name, ws.top.config.dir)
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
