"""The Typer application and its command groups; command modules register on these.

Every command registered here turns a ``SpecworksError`` into the error output
(``{"error": ...}`` with ``--json``) and exit code 1, so commands just let them raise.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

import typer

from ..core.errors import SpecworksError
from .output import fail


# @req REQ-CLI-001
def _reporting_errors(fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(fn)  # Typer reads the parameters from the wrapped signature
    def command(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except SpecworksError as exc:
            fail(str(exc), kwargs.get("as_json", False))

    return command


class App(typer.Typer):
    def command(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:  # type: ignore[override]
        register = super().command(*args, **kwargs)
        return lambda fn: register(_reporting_errors(fn))


app = App(help="Spec-driven development: refine → specify → design → test → code → review → validate → close.")
module_app = App(help="Manage modules (sub-projects linked to this one, like git submodules).")
spec_app = App(help="Read capabilities and their living specs.")
task_app = App(help="List and tick the tasks of a change (tasks.md).")
capability_app = App(help="Register capabilities (durable behaviours owned by a code folder).")

app.add_typer(module_app, name="module")
app.add_typer(spec_app, name="spec")
app.add_typer(task_app, name="task")
app.add_typer(capability_app, name="capability")
