"""Specs and traceability: check, trace, spec show/list and diagrams."""

from __future__ import annotations

from pathlib import Path

import typer
from pyd2 import DARK_THEMES, THEMES

from ..core.config import theme_name
from ..specs.capabilities import describe, resolve_ref, workspace_capabilities
from ..specs.trace import Analysis, to_markdown, write_traceability
from ..tools.diagrams import DiagramError, diagrams_in, find_d2, render, state
from .app import app, spec_app
from .output import ChangeOpt, JsonOpt, change_dict, emit, fail, require_change, workspace


@app.command("check")
def check_cmd(
    change: str = ChangeOpt,
    strict: bool = typer.Option(False, "--strict", help="Treat warnings as errors."),
    as_json: bool = JsonOpt,
) -> None:
    """Check a change's proposal, delta specs and tasks (IDs, SHALL/MUST, scenarios, coverage)."""
    ws, mod, ch = require_change(change, as_json)
    issues = Analysis(ws, ch).issues
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
    change: str = ChangeOpt,
    write: bool = typer.Option(False, "--write", help="Write traceability.md in the change folder."),
    as_json: bool = JsonOpt,
) -> None:
    """Requirement -> acceptance criterion -> task -> test (@ac) -> code (@req) matrix of a change."""
    ws, mod, ch = require_change(change, as_json)
    analysis = Analysis(ws, ch)
    rows, found = analysis.rows, analysis.gaps
    markdown = to_markdown(mod.qualify(ch.name), rows, found)
    written = ws.rel(write_traceability(ch, markdown)) if write else None
    data = {
        **change_dict(ws, mod, ch),
        "rows": [vars(r) for r in rows],
        "gaps": found,
        "unknownTags": [{"id": t.id, "where": t.where, **({"hint": t.hint} if t.hint else {})} for t in analysis.unknown_tags],
        "specErrors": len(analysis.spec_errors),
        "written": written,
    }
    text = markdown + (f"\nwrote {written}" if written else "")
    emit(data, as_json, text)


@spec_app.command("show")
def spec_show(
    ref: str = typer.Argument(..., help="Capability name, or module:name for another module."),
    no_scenarios: bool = typer.Option(False, "--no-scenarios", help="Only requirement IDs and titles."),
    as_json: bool = JsonOpt,
) -> None:
    """A capability's living spec, ID prefix, next free ID and delta path (also for a new capability)."""
    ws = workspace(as_json)
    cap = resolve_ref(ws, ref)
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
        data: dict[str, object] = {
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
        assert change is not None  # exactly one of --change / --dir, checked above
        ws, mod, ch = require_change(change, as_json)
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
