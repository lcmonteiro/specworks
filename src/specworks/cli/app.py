"""The Typer application and its command groups; command modules register on these."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Any

import typer
from typer.core import TyperGroup

from ..core.errors import SpecworksError
from .output import print_error


class SpecworksGroup(TyperGroup):
    """Reports any ``SpecworksError`` a command raises as ``error: ...`` (or JSON with ``--json``) and exit code 1.

    Commands only handle errors they turn into something else; everything else lands here.
    """

    def main(self, args: Sequence[str] | None = None, *rest: Any, **extra: Any) -> Any:
        argv = list(sys.argv[1:] if args is None else args)
        try:
            return super().main(args, *rest, **extra)
        except SpecworksError as exc:
            print_error(str(exc), "--json" in argv)
            sys.exit(1)


app = typer.Typer(cls=SpecworksGroup, help="Spec-driven development: refine → specify → design → test → code → review → validate → close.")
module_app = typer.Typer(help="Manage modules (sub-projects linked to this one, like git submodules).")
spec_app = typer.Typer(help="Read capabilities and their living specs.")
task_app = typer.Typer(help="List and tick the tasks of a change (tasks.md).")
capability_app = typer.Typer(help="Register capabilities (durable behaviours owned by a code folder).")

app.add_typer(module_app, name="module")
app.add_typer(spec_app, name="spec")
app.add_typer(task_app, name="task")
app.add_typer(capability_app, name="capability")
