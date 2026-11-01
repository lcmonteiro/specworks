"""Changes and their artifacts: new, status, phase, commit, instructions and tasks."""

from __future__ import annotations

import typer

from ..core.changes import PHASES, ChangeError, ChangeNotFound, commit_phase, create_change, set_phase
from ..core.git import GitError, branch_name, create_branch, current_branch, plan_branch, require_repo
from ..specs.merge import archive_change
from ..specs.tasks import read_tasks, set_done
from ..workflow.artifacts import artifact_states, half_progress, instructions
from ..workflow.review import detect_base
from .app import app, task_app
from .output import ChangeOpt, JsonOpt, change_dict, emit, require_change, resolve_archived, resolve_change, workspace


# @req REQ-CLI-006
# @req REQ-CLI-015
@app.command()
def new(
    name: str,
    module: str | None = typer.Option(None, "--module", "-m", help="Create it in this module instead of the current one."),
    branch: bool | None = typer.Option(
        None, "--branch/--no-branch", help="Create the change's branch, or stay on the current one, whatever the config's branch_per_change says."
    ),
    as_json: bool = JsonOpt,
) -> None:
    """Create a new change folder (phase: refine) in the current module, on its own branch unless branch_per_change is false."""
    ws = workspace(as_json)
    target = ws.module(module) if module is not None else ws.current
    require_repo(target.root)
    plan = None
    stayed_on = None
    if branch is None:
        branch = ws.top.config.branch_per_change  # only the top level's setting counts
    if branch:
        try:
            base = detect_base(target.root)
        except GitError:
            base = None
        plan = plan_branch(target.root, branch_name(target.qualify(name)), base)
    else:
        stayed_on = current_branch(target.root)
    change = create_change(target.config, name, ws.root)
    if plan is not None:
        create_branch(target.root, plan)
    data = {**change_dict(ws, target, change), "branch": plan.name if plan else None, "startedFrom": plan.started_from if plan else None, "stayedOn": stayed_on}
    lines = [f"created {ws.rel(change.path)}"]
    if plan is not None:
        lines.append(f"branch  {plan.name}")
        if plan.started_from is not None:
            lines.append(f"started from {plan.started_from}, not the base branch")
    if stayed_on is not None:
        lines.append(f"stayed on {stayed_on}")
    emit(data, as_json, "\n".join(lines))


# @req REQ-CLI-002
@app.command()
def status(change: str = ChangeOpt, as_json: bool = JsonOpt) -> None:
    """Phase and artifact states (done / ready / blocked) of a change, active or archived."""
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
    except ChangeNotFound:
        mod, ch = resolve_archived(ws, change)
    states = artifact_states(ch)
    data = {**change_dict(ws, mod, ch), "phases": list(PHASES), "artifacts": states}
    head = f"{mod.qualify(ch.name)} (phase: {ch.phase})"
    if (halves := half_progress(ch)) is not None:
        data["halves"] = halves
        head += ": " + ", ".join(f"{half} {n['done']}/{n['total']}" for half, n in halves.items())
    if data.get("archived"):
        head += f", abandoned: {ch.abandoned}" if ch.abandoned else ""
        head += f", archived at {ws.rel(ch.path)}"
    text = "\n".join([head] + [f"  [{s['status']:^7}] {s['generates']}" for s in states])
    emit(data, as_json, text)


# @req REQ-CLI-006
@app.command()
def abandon(
    change: str = ChangeOpt,
    reason: str = typer.Option(..., "--reason", help="Why the change is dropped; kept in its archived metadata."),
    as_json: bool = JsonOpt,
) -> None:
    """Archive a change without merging its specs: it will not be built. Its name stays taken."""
    ws, mod, ch = require_change(change, as_json)
    if not reason.strip():
        raise ChangeError("say why with --reason (e.g. --reason 'replaced by add-deadlines')")
    phase = ch.phase
    ch.path = archive_change(ch, mod.config.archive_path, abandoned=reason.strip())
    emit(change_dict(ws, mod, ch), as_json, f"{mod.qualify(ch.name)}: abandoned in phase {phase}, archived at {ws.rel(ch.path)}")


# @req REQ-CLI-006
@app.command()
def phase(
    to: str = typer.Argument(..., help=f"One of: {', '.join(p for p in PHASES if p != 'done')} (done is set by `specworks close`; test and code are the halves of implement)."),
    old_to: str | None = typer.Argument(None, hidden=True),  # the order before `phase <phase> --change <ref>`
    change: str | None = typer.Option(None, "--change", "-c", help="Change name or module:name."),
    as_json: bool = JsonOpt,
) -> None:
    """Move a change to another phase, unchecked (`specworks start` checks the gates first)."""
    if old_to is not None or change is None:
        # `phase <ref> <phase>` was the order before `start` and `gate` set `<phase> --change <ref>`.
        hint = f"specworks phase {old_to} --change {to}" if old_to is not None else f"specworks phase {to} --change <ref>"
        raise ChangeError(f"give the change with --change, like `specworks start` and `specworks gate`: {hint}")
    ws, mod, ch = require_change(change, as_json)
    set_phase(ch, to, ws.root)
    emit(change_dict(ws, mod, ch), as_json, f"{mod.qualify(ch.name)}: phase → {ch.phase}")


# @req REQ-CLI-012
@app.command()
def commit(
    change: str = ChangeOpt,
    message: str | None = typer.Option(None, "--message", help="The commit subject (default: `<ref>: <phase>`)."),
    trailer: list[str] | None = typer.Option(None, "--trailer", help="A trailer line, e.g. 'Co-Authored-By: A <a@x>'; repeat it for more, kept in order."),
    as_json: bool = JsonOpt,
) -> None:
    """Commit the change's phase: its folder and the files changed since the phase started. Never pushes.

    With no active change of that name, it commits the newest archived one (after `specworks close`), subject
    `<ref>: close`. `--json` returns ref, commit (null when nothing was committed), subject, committed, leftOut and
    alreadyDirty.
    """
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
    except ChangeNotFound:
        mod, ch = resolve_archived(ws, change)
    ref = mod.qualify(ch.name)
    result = commit_phase(ws.root, ref, ch, message, trailer or ())
    data = {
        "ref": ref,
        "commit": result.commit,
        "subject": result.subject,
        "committed": result.committed,
        "leftOut": result.left_out,
        "alreadyDirty": result.already_dirty,
    }
    if result.commit is None:
        lines = [f"nothing to commit for {ref}: no file changed since the phase started"]
    else:
        lines = [f"{result.commit} {result.subject}", *(f"  {p}" for p in result.committed)]
    lines += [f"left out (unchanged since the phase started): {p}" for p in result.left_out]
    lines += [f"already dirty when the phase started: {p}" for p in result.already_dirty]
    emit(data, as_json, "\n".join(lines))


# @req REQ-CLI-006
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
