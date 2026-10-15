"""The Typer application and its command groups; command modules register on these."""

from __future__ import annotations

import typer

app = typer.Typer(help="Spec-driven development: refine → specify → design → test → code → review → validate → close.")
module_app = typer.Typer(help="Manage modules (sub-projects linked to this one, like git submodules).")
spec_app = typer.Typer(help="Read capabilities and their living specs.")
task_app = typer.Typer(help="List and tick the tasks of a change (tasks.md).")
capability_app = typer.Typer(help="Register capabilities (durable behaviours owned by a code folder).")

app.add_typer(module_app, name="module")
app.add_typer(spec_app, name="spec")
app.add_typer(task_app, name="task")
app.add_typer(capability_app, name="capability")
