"""Changes and their artifacts: new, status, phase, instructions and tasks."""

from __future__ import annotations

import typer

from ..core.changes import PHASES, create_change, set_phase
from ..specs.tasks import read_tasks, set_done
from ..workflow.artifacts import artifact_states, instructions
from .app import app, task_app
from .output import ChangeOpt, JsonOpt, change_dict, emit, require_change, workspace


@app.command()
def new(
    name: str,
    module: str | None = typer.Option(None, "--module", "-m", help="Create it in this module instead of the current one."),
    as_json: bool = JsonOpt,
) -> None:
    """Create a new change folder (phase: refine) in the current module."""
    ws = workspace(as_json)
    target = ws.module(module) if module is not None else ws.current
    change = create_change(target.config, name)
    emit(change_dict(ws, target, change), as_json, f"created {ws.rel(change.path)}")


@app.command()
def status(change: str = ChangeOpt, as_json: bool = JsonOpt) -> None:
    """Phase and artifact states (done / ready / blocked) of a change."""
    ws, mod, ch = require_change(change, as_json)
    states = artifact_states(ch)
    data = {**change_dict(ws, mod, ch), "phases": list(PHASES), "artifacts": states}
    text = "\n".join([f"{mod.qualify(ch.name)} (phase: {ch.phase})"] + [f"  [{s['status']:^7}] {s['generates']}" for s in states])
    emit(data, as_json, text)


@app.command()
def phase(
    name: str = typer.Argument(..., help="Change name or module:name."),
    to: str = typer.Argument(..., help=f"One of: {', '.join(p for p in PHASES if p != 'done')} (done is set by `specworks close`)."),
    as_json: bool = JsonOpt,
) -> None:
    """Move a change to another phase."""
    ws, mod, ch = require_change(name, as_json)
    set_phase(ch, to)
    emit(change_dict(ws, mod, ch), as_json, f"{mod.qualify(ch.name)}: phase → {ch.phase}")


@app.command("skip-specs")
def skip_specs(
    change: str = ChangeOpt,
    off: bool = typer.Option(False, "--off", help="The change does change behaviour after all: delta specs are required again."),
    as_json: bool = JsonOpt,
) -> None:
    """Mark a change with no behaviour change (refactor, tooling, docs): it has no delta specs."""
    ws, mod, ch = require_change(change, as_json)
    ch.skip_specs = not off
    ch.save()
    state = "skips delta specs" if ch.skip_specs else "needs delta specs"
    emit(change_dict(ws, mod, ch), as_json, f"{mod.qualify(ch.name)}: {state}")


@app.command("instructions")
def instructions_cmd(
    artifact: str,
    change: str = ChangeOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Template, rules and output path for writing one artifact of a change."""
    ws, mod, ch = require_change(change, as_json)
    data = instructions(ws, mod, ch, artifact)
    text = f"# {data['artifact']} → {data['outputPath']}\n\n{data['instruction']}\n---\n{data['template']}"
    emit(data, as_json, text)


def _emit_tasks(ws, mod, ch, tasks, as_json: bool) -> None:
    done = sum(t.done for t in tasks)
    data = {**change_dict(ws, mod, ch), "done": done, "total": len(tasks), "tasks": [t.to_dict() for t in tasks]}
    lines = [f"[{'x' if t.done else ' '}] {t.num} {t.text}" for t in tasks] + [f"{done}/{len(tasks)} done"]
    emit(data, as_json, "\n".join(lines))


@task_app.command("list")
def task_list(
    change: str = ChangeOpt,
    pending: bool = typer.Option(False, "--pending", help="Only tasks not done yet."),
    as_json: bool = JsonOpt,
) -> None:
    """List the tasks of a change with their IDs and state."""
    ws, mod, ch = require_change(change, as_json)
    tasks = read_tasks(ch.path)
    _emit_tasks(ws, mod, ch, [t for t in tasks if not (pending and t.done)], as_json)


def _set(change: str, nums: list[str], done: bool, as_json: bool) -> None:
    ws, mod, ch = require_change(change, as_json)
    set_done(ch.path, nums, done)
    tasks = read_tasks(ch.path)
    _emit_tasks(ws, mod, ch, tasks, as_json)


@task_app.command("done")
def task_done(
    nums: list[str] = typer.Argument(..., help="Task numbers, e.g. 1.1 1.2."),
    change: str = ChangeOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Tick tasks as done (- [x])."""
    _set(change, nums, True, as_json)


@task_app.command("undo")
def task_undo(
    nums: list[str] = typer.Argument(..., help="Task numbers, e.g. 1.1 1.2."),
    change: str = ChangeOpt,
    as_json: bool = JsonOpt,
) -> None:
    """Mark tasks as not done (- [ ])."""
    _set(change, nums, False, as_json)
