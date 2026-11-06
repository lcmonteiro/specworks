"""Keeping a peer in its workspace: file tools rooted in it, and a shell that runs there and refuses ``git push``."""

from __future__ import annotations

import re
from pathlib import Path

from deepagents.backends import LocalShellBackend
from deepagents.backends.protocol import ExecuteResponse

PUSH_RE = re.compile(r"\bgit\b.*\bpush\b")


def refuses(command: str) -> bool:
    """Whether the shell refuses ``command`` (a ``git push``). Implements REQ-HARNESS-008."""
    raise NotImplementedError


class ConfinedShell(LocalShellBackend):
    """A ``LocalShellBackend`` in virtual mode rooted in a workspace, refusing ``git push``. Implements REQ-HARNESS-008."""

    def __init__(self, root: Path) -> None:
        """Rooted in ``root`` (``root_dir=root``, ``virtual_mode=True``)."""
        raise NotImplementedError

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Run ``command`` in the workspace; a refused one is an error response and nothing runs. Implements REQ-HARNESS-008."""
        raise NotImplementedError


def confined(root: Path) -> ConfinedShell:
    """The file and shell backend of a peer whose workspace is ``root``. Implements REQ-HARNESS-008."""
    raise NotImplementedError
