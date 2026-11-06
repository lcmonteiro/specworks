"""Keeping a peer in its workspace: file tools rooted in it, and a shell that runs there and refuses ``git push``."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path, PurePosixPath

from deepagents.backends import LocalShellBackend
from deepagents.backends.protocol import (
    DeleteResult,
    EditResult,
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
    GlobResult,
    GrepResult,
    LsResult,
    ReadResult,
    SandboxBackendProtocol,
    WriteResult,
)

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


class PeerShell(SandboxBackendProtocol):
    """The one backend a peer's Deep Agent holds: every file or shell call goes to ``confined(root_of())`` at call time.

    The folder follows the peer's workspace, so a ``/workspace`` switch moves the file tools and the shell within the same
    run. Implements REQ-HARNESS-006, REQ-HARNESS-008.
    """

    def __init__(self, root_of: Callable[[], Path]) -> None:
        """Following ``root_of``, called on every file or shell call (the peer's workspace folder)."""
        self.root_of = root_of
        #: The confined shell of each folder the peer has worked in.
        self._shells: dict[Path, ConfinedShell] = {}

    def current(self) -> ConfinedShell:
        """``confined(root_of())``, one kept per folder. Implements REQ-HARNESS-006, REQ-HARNESS-008."""
        raise NotImplementedError

    @property
    def id(self) -> str:
        """The identifier of this backend."""
        raise NotImplementedError

    def ls(self, path: str) -> LsResult:
        """``ls`` in the current workspace."""
        raise NotImplementedError

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> ReadResult:
        """``read`` in the current workspace."""
        raise NotImplementedError

    def grep(self, pattern: str, path: str | None = None, glob: str | None = None, *, max_count: int | None = None) -> GrepResult:
        """``grep`` in the current workspace."""
        raise NotImplementedError

    def glob(self, pattern: str, path: str | None = None) -> GlobResult:
        """``glob`` in the current workspace."""
        raise NotImplementedError

    def write(self, file_path: str, content: str) -> WriteResult:
        """``write`` in the current workspace."""
        raise NotImplementedError

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:  # noqa: FBT001, FBT002 - the protocol's signature
        """``edit`` in the current workspace."""
        raise NotImplementedError

    def delete(self, file_path: str) -> DeleteResult:
        """``delete`` in the current workspace."""
        raise NotImplementedError

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """``upload_files`` into the current workspace."""
        raise NotImplementedError

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """``download_files`` from the current workspace."""
        raise NotImplementedError

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """``execute`` in the current workspace (a ``git push`` is refused there)."""
        raise NotImplementedError
