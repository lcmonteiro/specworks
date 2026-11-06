"""Keeping a peer in its workspace: file tools rooted in it, and a shell that runs there and refuses ``git push``."""

from __future__ import annotations

import os
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

#: A push: ``git``, then any global options (``-C x``, ``--no-pager``, ``-c a=b``), then the ``push`` subcommand.
PUSH_RE = re.compile(r"\bgit(\s+-{1,2}\S+(\s+[^-\s]\S*)?)*\s+push\b")

#: The variables a peer's shell never gets: the model's and the tracing keys.
HIDDEN_ENV = ("SPECWORKS_MODEL_", "SPECWORKS_LANGFUSE_")


class OutsideWorkspaceError(PermissionError):
    """A path that leads outside the workspace; an ``OSError``, so the backend turns it into an error result."""


# @req REQ-HARNESS-010
def shell_env() -> dict[str, str]:
    """The environment of a peer's shell: this process's, without ``HIDDEN_ENV``. Implements REQ-HARNESS-010."""
    return {k: v for k, v in os.environ.items() if not k.startswith(HIDDEN_ENV)}


# @req REQ-HARNESS-008
def refuses(command: str) -> bool:
    """Whether the shell refuses ``command`` (a ``git push``). Implements REQ-HARNESS-008."""
    return PUSH_RE.search(command) is not None


# @req REQ-HARNESS-008
class ConfinedShell(LocalShellBackend):
    """A ``LocalShellBackend`` in virtual mode rooted in a workspace, refusing ``git push``. Implements REQ-HARNESS-008."""

    def __init__(self, root: Path) -> None:
        """Rooted in ``root`` (``root_dir=root``, ``virtual_mode=True``)."""
        # Virtual mode maps every file path under root and rejects `..` and paths outside it. The shell gets no model key.
        super().__init__(root_dir=root, virtual_mode=True, env=shell_env(), inherit_env=False)

    def _resolve_path(self, key: str) -> Path:
        """``key`` inside the workspace; a path outside it is refused (``OutsideWorkspaceError``) rather than mapped inside.

        Virtual mode reads ``/src/a.py`` as ``<root>/src/a.py``, and also maps a real path such as ``/tmp/x`` there, so a
        write to it would land inside the workspace and say nothing. A path under the workspace's real folder is that file;
        a path with a drive, or whose first part is a folder of the machine's root that the workspace does not have, leads
        outside. The refusal is an ``OSError``, which every file operation of the backend returns as its error result,
        where a ``ValueError`` would escape them. Implements REQ-HARNESS-008.
        """
        given = Path(key)
        if given.is_absolute():
            try:
                key = "/" + given.resolve().relative_to(self.cwd).as_posix()
            except ValueError:
                first = PurePosixPath(key.replace("\\", "/")).parts[1:2]
                if given.drive or (first and Path(given.anchor, first[0]).exists() and not (self.cwd / first[0]).exists()):
                    raise OutsideWorkspaceError(f"path {key} is outside the workspace") from None
        try:
            return super()._resolve_path(key)
        except ValueError as exc:  # `..`, `~`, or a path that resolves outside the root
            raise OutsideWorkspaceError(f"path {key} is outside the workspace ({exc})") from None

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Run ``command`` in the workspace; a refused one is an error response and nothing runs. Implements REQ-HARNESS-008."""
        if refuses(command):
            return ExecuteResponse(output="Error: git push is refused in the harness: the user pushes after the run.", exit_code=1, truncated=False)
        return super().execute(command, timeout=timeout)


# @req REQ-HARNESS-008
def confined(root: Path) -> ConfinedShell:
    """The file and shell backend of a peer whose workspace is ``root``. Implements REQ-HARNESS-008."""
    return ConfinedShell(root)


# @req REQ-HARNESS-006
# @req REQ-HARNESS-008
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
        root = self.root_of()
        shell = self._shells.get(root)
        if shell is None:
            shell = self._shells[root] = confined(root)
        return shell

    @property
    def id(self) -> str:
        """The identifier of this backend."""
        return f"peer-shell-{id(self):x}"

    def ls(self, path: str) -> LsResult:
        """``ls`` in the current workspace."""
        return self.current().ls(path)

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> ReadResult:
        """``read`` in the current workspace."""
        return self.current().read(file_path, offset, limit)

    def grep(self, pattern: str, path: str | None = None, glob: str | None = None, *, max_count: int | None = None) -> GrepResult:
        """``grep`` in the current workspace."""
        return self.current().grep(pattern, path, glob, max_count=max_count)

    def glob(self, pattern: str, path: str | None = None) -> GlobResult:
        """``glob`` in the current workspace."""
        return self.current().glob(pattern, path)

    def write(self, file_path: str, content: str) -> WriteResult:
        """``write`` in the current workspace."""
        return self.current().write(file_path, content)

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:  # noqa: FBT001, FBT002 - the protocol's signature
        """``edit`` in the current workspace."""
        return self.current().edit(file_path, old_string, new_string, replace_all)

    def delete(self, file_path: str) -> DeleteResult:
        """``delete`` in the current workspace."""
        return self.current().delete(file_path)

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """``upload_files`` into the current workspace."""
        return self.current().upload_files(files)

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """``download_files`` from the current workspace."""
        return self.current().download_files(paths)

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """``execute`` in the current workspace (a ``git push`` is refused there)."""
        return self.current().execute(command, timeout=timeout)
