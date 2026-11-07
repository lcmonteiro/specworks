"""Workspaces: the main checkout the phase peers share, a git worktree for ``test``, a ``run`` operation, and ``/merge``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from chatinho import LOCAL, HookExecute, Reply, require, tool
from chatinho.workspaces import GitWorktrees, Workspace, WorkspaceView, operation

from ..core.errors import SpecworksError
from ..core.workspace import Workspace as SpecworksProject

if TYPE_CHECKING:
    from .backend import GitBackend

#: The peers that work in a git worktree of their own; every other peer works in the main checkout.
WORKTREE_PEERS: frozenset[str] = frozenset({"test"})

#: How long ``run`` waits for a command, in seconds, before it stops it (read at call time).
RUN_TIMEOUT: float = 600.0


# @req REQ-HARNESS-006
# @req REQ-HARNESS-007
class WorkspaceError(SpecworksError):
    """A workspace refused: a merge aborted on a conflict (``files``).

    Implements REQ-HARNESS-006, REQ-HARNESS-007.
    """

    def __init__(self, message: str, files: list[Path] | None = None) -> None:
        super().__init__(message)
        self.files: list[Path] = list(files or [])


class SpecworksWorkspace(Workspace):
    """chatinho's ``Workspace`` with a ``run`` operation, which agents get as ``ws_run``. Implements REQ-HARNESS-008."""

    @operation("Run a shell command in the workspace and return its output and exit code", writes=True)
    async def run(self, command: str) -> str:
        """Run ``command`` through the platform shell in the workspace's folder, with ``shell_env()``.

        Returns ``"exit code <n>\\n<output>"`` (stderr merged into stdout). Raises ``PermissionError`` for a ``git push``
        (nothing runs) and ``TimeoutError`` once it has run past ``RUN_TIMEOUT`` (it is killed). Implements REQ-HARNESS-008.
        """
        raise NotImplementedError


class SpecworksWorktrees(GitWorktrees):
    """The provider: one main checkout every phase peer shares, and a worktree for each of ``WORKTREE_PEERS``.

    Implements REQ-HARNESS-006.
    """

    def __init__(self, ws: SpecworksProject) -> None:
        """Over the repository of ``ws`` (``repo=ws.root``), with ``SpecworksWorkspace`` as the owner's workspace."""
        super().__init__(ws.root, workspace=SpecworksWorkspace)
        self.ws = ws

    async def provision(self, owner: str | None, name: str, create: bool = True) -> WorkspaceView:
        """``name``'s workspace for ``owner``: the main checkout for a name not in ``WORKTREE_PEERS``, else its worktree.

        The main checkout is a ``SpecworksWorkspace`` when ``owner`` is a checkout peer too, a ``WorkspaceView`` otherwise.
        A worktree created now starts from the branch the checkout has now. Implements REQ-HARNESS-006.
        """
        raise NotImplementedError

    async def current_branch(self) -> str:
        """The branch the main checkout has checked out, else its ``HEAD`` commit. Implements REQ-HARNESS-006."""
        raise NotImplementedError


@tool("merge", "Merge a workspace into the main checkout: /merge <name>")
@require(HookExecute)
class MergeCommand:
    """``/merge <name>``: the user merges a worktree into the main checkout for the run's change, then removes it.

    Implements REQ-HARNESS-007.
    """

    def __init__(self, provider: SpecworksWorktrees, backend: GitBackend) -> None:
        self.provider = provider
        self.backend = backend

    async def execute(self, args: str = "", by: int = LOCAL, **kwargs: Any) -> Reply:
        """Merge the workspace named in ``args``; every refusal is an error reply and changes nothing. Implements REQ-HARNESS-007."""
        raise NotImplementedError
