"""`specworks harness`: the specworks flow as a chatinho chat in the terminal (needs the `harness` extra)."""

from __future__ import annotations

import typer

from .app import app

#: Why the command cannot run without its extra.
EXTRA_MISSING = "specworks harness needs the harness extra on Python 3.12 or later: install specworks[harness]"


@app.command()
def harness(
    request: str | None = typer.Argument(None, help="The first message, said to refine (or, with --change, to the peer of its phase)."),
    change: str | None = typer.Option(None, "--change", "-c", help="Change name or module:name to run on, continuing its conversation."),
) -> None:
    """Open the harness chat: one agent peer per skill, handing work to each other (needs specworks[harness], Python 3.12+).

    Implements REQ-CLI-022.
    """
    # The harness is imported here only, so no other command loads chatinho or deepagents.
    raise NotImplementedError
