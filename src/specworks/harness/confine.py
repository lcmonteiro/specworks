"""Keeping a peer in its workspace: file tools rooted in it, and a shell that runs there and refuses ``git push``."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from deepagents.backends import LocalShellBackend
from deepagents.backends.protocol import ExecuteResponse

PUSH_RE = re.compile(r"\bgit\b.*\bpush\b")


# @req REQ-HARNESS-008
def refuses(command: str) -> bool:
    """Whether the shell refuses ``command`` (a ``git push``). Implements REQ-HARNESS-008."""
    return PUSH_RE.search(command) is not None


# @req REQ-HARNESS-008
class ConfinedShell(LocalShellBackend):
    """A ``LocalShellBackend`` in virtual mode rooted in a workspace, refusing ``git push``. Implements REQ-HARNESS-008."""

    def __init__(self, root: Path) -> None:
        """Rooted in ``root`` (``root_dir=root``, ``virtual_mode=True``)."""
        # Virtual mode maps every file path under root and rejects `..` and paths outside it.
        super().__init__(root_dir=root, virtual_mode=True, inherit_env=True)

    def _resolve_path(self, key: str) -> Path:
        """``key`` inside the workspace; a real absolute path outside it is refused (``ValueError``) rather than mapped inside.

        Virtual mode reads ``/src/a.py`` as ``<root>/src/a.py``, and also maps a real path such as ``/tmp/x`` there, so a
        write to it would land inside the workspace and say nothing. A path under the workspace's real folder is that file;
        a path with a drive, or whose first part is a folder of the machine's root that the workspace does not have, leads
        outside. Implements REQ-HARNESS-008.
        """
        given = Path(key)
        if given.is_absolute():
            try:
                key = "/" + given.resolve().relative_to(self.cwd).as_posix()
            except ValueError:
                first = PurePosixPath(key.replace("\\", "/")).parts[1:2]
                if given.drive or (first and Path(given.anchor, first[0]).exists() and not (self.cwd / first[0]).exists()):
                    raise ValueError(f"Path {key} is outside the workspace {self.cwd}") from None
        return super()._resolve_path(key)

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Run ``command`` in the workspace; a refused one is an error response and nothing runs. Implements REQ-HARNESS-008."""
        if refuses(command):
            return ExecuteResponse(output="Error: git push is refused in the harness: the user pushes after the run.", exit_code=1, truncated=False)
        return super().execute(command, timeout=timeout)


# @req REQ-HARNESS-008
def confined(root: Path) -> ConfinedShell:
    """The file and shell backend of a peer whose workspace is ``root``. Implements REQ-HARNESS-008."""
    return ConfinedShell(root)
