"""`specworks harness`: the specworks flow as a chatinho chat in the terminal (needs the `harness` extra)."""

from __future__ import annotations

import sys

import typer

from ..core.errors import SpecworksError
from .app import app
from .output import resolve_change, workspace

#: Why the command cannot run without its extra.
EXTRA_MISSING = "specworks harness needs the harness extra on Python 3.12 or later: install specworks[harness]"


# @req REQ-CLI-022
@app.command()
def harness(
    request: str | None = typer.Argument(None, help="The first message, said to refine (or, with --change, to the peer of its phase)."),
    change: str | None = typer.Option(None, "--change", "-c", help="Change name or module:name to run on, continuing its conversation."),
) -> None:
    """Open the harness chat: one agent peer per skill, handing work to each other (needs the harness extra, Python 3.12+).

    Implements REQ-CLI-022.
    """
    if sys.version_info < (3, 12):
        raise SpecworksError(EXTRA_MISSING)
    # The harness is imported here only, so no other command loads chatinho or deepagents.
    try:
        from ..harness import run_harness
    except ImportError:
        raise SpecworksError(EXTRA_MISSING) from None
    ws = workspace(False)
    run_harness(ws, request, resolve_change(ws, change)[1] if change is not None else None)
