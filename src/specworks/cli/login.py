"""
`specworks login`: store a Copilot login for the harness (needs the `harness` extra).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer

from specworks.cli.app import app
from specworks.cli.output import emit, fail, workspace

if TYPE_CHECKING:
    from specworks.harness.logins import Scope

#: Why the command cannot run without its extra.
EXTRA_MISSING = "specworks login needs the harness extra: install specworks[harness]"


# @req REQ-CLI-023
@app.command()
def login(
    provider: str = typer.Argument(..., help="The provider to log in to: copilot."),
    local: bool = typer.Option(False, "--local", help="Store the login for this project only."),
    global_: bool = typer.Option(False, "--global", help="Store the login for every project (the default)."),
    force: bool = typer.Option(False, "--force", help="Log in again even when the stored login works."),
    ghe_host: str = typer.Option("", "--ghe-host", help="A GitHub Enterprise host, empty for github.com."),
    as_json: bool = typer.Option(False, "--json", help="Print the result as JSON."),
) -> None:
    """
    Log in to GitHub Copilot with the device flow and store the login outside the project, for ``specworks harness``.

    Implements REQ-CLI-023.
    """
    if provider != "copilot":
        fail(f"unknown provider {provider!r}: the only one is copilot", as_json)
    if local and global_:
        raise typer.BadParameter("--local and --global cannot be used together")
    # The harness is imported here only, so no other command loads its dependencies.
    try:
        from specworks.harness.copilot import CopilotLoginError, log_in
    except ImportError:
        fail(EXTRA_MISSING, as_json)
    scope: Scope = "local" if local else "global"
    root = workspace(as_json).root if local else None

    def prompt(uri: str, code: str) -> None:
        typer.echo(f"Open {uri} and enter the code {code}", err=True)

    try:
        result = log_in(scope, root, force=force, ghe_host=ghe_host, prompt=prompt)
    except CopilotLoginError as error:
        fail(str(error), as_json)
    verb = "Reused the stored" if result.reused else "Stored a new"
    emit({"provider": provider, "scope": result.scope, "reused": result.reused}, as_json, f"{verb} Copilot login ({result.scope}).")
