"""specworks command line interface.

Every command that agents read supports ``--json``. When no project is found the
JSON answer is ``{"root": null, ...}`` with exit code 1, so a skill can tell
"not set up" apart from a crash.

Paths in the output are relative to the workspace root (the top-level project),
which is printed as ``root``.
"""

from __future__ import annotations

import json
import sys

import typer

from ..core.changes import ChangeError
from ..core.config import ConfigError
from .app import app

# Importing the command modules registers their commands; this order is the order of `--help`.
# isort: off
from . import project  # noqa: E402, F401
from . import changes  # noqa: E402, F401
from . import specs  # noqa: E402, F401
from . import workflow  # noqa: E402, F401
# isort: on

__all__ = ["app", "main"]


def main() -> None:
    """Run the CLI; a broken config or change file anywhere in the workspace is an error message, not a traceback."""
    try:
        app()
    except (ConfigError, ChangeError) as exc:
        if "--json" in sys.argv[1:]:
            typer.echo(json.dumps({"error": str(exc)}, indent=2))
        else:
            typer.echo(f"error: {exc}", err=True)
        sys.exit(1)
