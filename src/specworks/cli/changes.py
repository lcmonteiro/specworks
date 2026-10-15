"""Changes and their artifacts: new, status, phase, instructions and tasks."""

from __future__ import annotations

import typer

from ..core.changes import PHASES, ChangeError, create_change, set_phase
from ..core.config import ConfigError
from ..specs.tasks import TaskError, read_tasks, set_done
from ..workflow.artifacts import WorkflowError, artifact_states, instructions
from .app import app, task_app
from .output import JsonOpt, change_dict, emit, fail, resolve_change, workspace


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
