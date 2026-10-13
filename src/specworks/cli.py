"""specworks command line interface.

Every command that agents read supports ``--json``. When no project is found the
JSON answer is ``{"root": null, ...}`` with exit code 1, so a skill can tell
"not set up" apart from a crash.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import NoReturn

import typer

from . import __version__
from .changes import PHASES, ChangeError, create_change, list_changes, load_change, set_phase
from .config import CONFIG_FILE, DEFAULT_CONFIG, Config, ConfigError, find_root, load_config
from .skills import install_skills
from .workflow import WorkflowError, artifact_states, instructions

app = typer.Typer(help="Spec-driven development: refine → propose → tests → code → review → verify → done.")

JsonOpt = typer.Option(False, "--json", help="Machine-readable output.")


def emit(data: dict, as_json: bool, text: str) -> None:
    typer.echo(json.dumps(data, indent=2) if as_json else text)


def fail(message: str, as_json: bool, **extra) -> NoReturn:
    if as_json:
        typer.echo(json.dumps({"error": message, **extra}, indent=2))
    else:
        typer.echo(f"error: {message}", err=True)
    raise typer.Exit(1)


def project(as_json: bool) -> Config:
    root = find_root()
    if root is None:
        fail(
            f"no {CONFIG_FILE} found in this directory or its parents",
            as_json,
            root=None,
            fix="run `specworks init` at the repository root",
        )
    try:
        return load_config(root)
    except ConfigError as exc:
        fail(str(exc), as_json, root=str(root))


@app.command()
def version() -> None:
    """Print the specworks version."""
    typer.echo(__version__)


@app.command()
def init(
    path: Path = typer.Argument(Path("."), help="Project root."),
    skills_dir: Path = typer.Option(Path(".claude/skills"), help="Where to install agent skills, relative to root."),
    no_skills: bool = typer.Option(False, "--no-skills", help="Do not install agent skills."),
) -> None:
    """Create specworks.yaml and the changes folder, and install the agent skills."""
    root = path.resolve()
    config_file = root / CONFIG_FILE
    if not config_file.exists():
        config_file.write_text(DEFAULT_CONFIG, encoding="utf-8")
        typer.echo(f"created {CONFIG_FILE}")
    cfg = load_config(root)
    cfg.archive_path.mkdir(parents=True, exist_ok=True)
    typer.echo(f"ready   {cfg.changes_dir}/")
    if not no_skills:
        for written in install_skills(root / skills_dir):
            typer.echo(f"skill   {written.relative_to(root)}")


@app.command()
def context(as_json: bool = JsonOpt) -> None:
    """Project context, capabilities (with their docs folders) and active changes."""
    cfg = project(as_json)
    data = {
        "root": str(cfg.root),
        "context": cfg.context,
        "changesDir": cfg.changes_dir,
        "docsDir": cfg.docs_dir,
        "capabilities": [c.to_dict(cfg.root, cfg.docs_dir) for c in cfg.capabilities.values()],
        "changes": [c.to_dict(cfg.root) for c in list_changes(cfg)],
    }
    lines = [f"root: {cfg.root}", "capabilities:"]
    lines += [f"  {c.name:<24} {c.path}" for c in cfg.capabilities.values()] or ["  (none)"]
    lines += ["changes:"] + ([f"  {c.name:<24} {c.phase}" for c in list_changes(cfg)] or ["  (none)"])
    emit(data, as_json, "\n".join(lines))


@app.command("list")
def list_cmd(as_json: bool = JsonOpt) -> None:
    """List active changes and their phase."""
    cfg = project(as_json)
    changes = list_changes(cfg)
    text = "\n".join(f"{c.name:<32} {c.phase}" for c in changes) or "no active changes"
    emit({"root": str(cfg.root), "changes": [c.to_dict(cfg.root) for c in changes]}, as_json, text)


@app.command()
def new(name: str, as_json: bool = JsonOpt) -> None:
    """Create a new change folder (phase: refine)."""
    cfg = project(as_json)
    try:
        change = create_change(cfg, name)
    except ChangeError as exc:
        fail(str(exc), as_json)
    emit(change.to_dict(cfg.root), as_json, f"created {change.path.relative_to(cfg.root)}")


@app.command()
def status(change: str = typer.Option(..., "--change", "-c"), as_json: bool = JsonOpt) -> None:
    """Phase and artifact states (done / ready / blocked) of a change."""
    cfg = project(as_json)
    try:
        ch = load_change(cfg, change)
    except ChangeError as exc:
        fail(str(exc), as_json)
    states = artifact_states(ch)
    data = {**ch.to_dict(cfg.root), "phases": list(PHASES), "artifacts": states}
    text = "\n".join([f"{ch.name} (phase: {ch.phase})"] + [f"  [{s['status']:^7}] {s['generates']}" for s in states])
    emit(data, as_json, text)


@app.command()
def phase(name: str, to: str = typer.Argument(..., help=f"One of: {', '.join(PHASES)}"), as_json: bool = JsonOpt) -> None:
    """Move a change to another phase."""
    cfg = project(as_json)
    try:
        ch = load_change(cfg, name)
        set_phase(ch, to)
    except ChangeError as exc:
        fail(str(exc), as_json)
    emit(ch.to_dict(cfg.root), as_json, f"{ch.name}: phase → {ch.phase}")


@app.command("instructions")
def instructions_cmd(
    artifact: str, change: str = typer.Option(..., "--change", "-c"), as_json: bool = JsonOpt
) -> None:
    """Template, rules and output path for writing one artifact of a change."""
    cfg = project(as_json)
    try:
        data = instructions(cfg, load_change(cfg, change), artifact)
    except (ChangeError, WorkflowError) as exc:
        fail(str(exc), as_json)
    text = f"# {data['artifact']} → {data['outputPath']}\n\n{data['instruction']}\n---\n{data['template']}"
    emit(data, as_json, text)


def main() -> None:
    app()
