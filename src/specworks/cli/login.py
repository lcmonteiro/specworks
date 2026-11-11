"""`specworks login`: store a Copilot login for the harness (needs the `harness` extra)."""

from __future__ import annotations

import typer

from specworks.cli.app import app


@app.command()
def login(
    provider: str = typer.Argument(..., help="The provider to log in to: copilot."),
    local: bool = typer.Option(False, "--local", help="Store the login for this project only."),
    global_: bool = typer.Option(False, "--global", help="Store the login for every project (the default)."),
    force: bool = typer.Option(False, "--force", help="Log in again even when the stored login works."),
    ghe_host: str = typer.Option("", "--ghe-host", help="A GitHub Enterprise host, empty for github.com."),
    as_json: bool = typer.Option(False, "--json", help="Print the result as JSON."),
) -> None:
    """Log in to GitHub Copilot with the device flow and store the login outside the project, for ``specworks harness``.

    Implements REQ-CLI-023.
    """
    raise NotImplementedError
