"""Workspaces: git worktrees on their own branches that peers work in, and the ``/workspace`` and ``/merge`` commands."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from chatinho import LOCAL, HookExecute, Reply, require, tool

from ..core.changes import Change
from ..core.errors import SpecworksError
from ..core.workspace import Module, Workspace
from ..workflow.merge import MergeResult

if TYPE_CHECKING:
    from .backend import GitBackend

WORKSPACES_DIR = ".specworks/workspaces"
MAIN = "main"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class WorkspaceError(SpecworksError):
    """A workspace refused: a bad or unknown name, or a merge aborted on a conflict (``files``).

    Implements REQ-HARNESS-006, REQ-HARNESS-007.
    """

    def __init__(self, message: str, files: list[Path] | None = None) -> None:
        super().__init__(message)
        self.files: list[Path] = list(files or [])


class Workspaces:
    """Each peer's workspace (``main``, the main checkout, until it opens another). Implements REQ-HARNESS-006, REQ-HARNESS-007."""

    def __init__(self, ws: Workspace, module: Module) -> None:
        raise NotImplementedError

    def path_of(self, peer: int) -> Path:
        """The folder of ``peer``'s workspace. Implements REQ-HARNESS-006."""
        raise NotImplementedError

    def name_of(self, peer: int) -> str:
        """The name of ``peer``'s workspace. Implements REQ-HARNESS-006."""
        raise NotImplementedError

    def branch_of(self, name: str) -> str:
        """The branch of the workspace ``name``: ``<main branch>--<name>``. Implements REQ-HARNESS-006."""
        raise NotImplementedError

    def open(self, name: str, peer: int) -> Path:
        """Create (or reuse) the workspace ``name`` and make it ``peer``'s; ``main`` is the main checkout.

        Raises ``WorkspaceError`` for a name that is not lowercase letters, digits and hyphens. Implements REQ-HARNESS-006.
        """
        raise NotImplementedError

    def merge(self, name: str, change: Change) -> MergeResult:
        """Merge the workspace's branch into the main checkout for ``change``, then remove it.

        Raises ``WorkspaceError`` for an unknown workspace (``no workspace '<name>'``) or a conflict (``files`` set).
        Implements REQ-HARNESS-007.
        """
        raise NotImplementedError


@tool("workspace", "Work in a git workspace: /workspace <name>, or /workspace main")
@require(HookExecute)
class WorkspaceCommand:
    """``/workspace <name>``: the invoking peer's workspace becomes ``<name>``. Implements REQ-HARNESS-006."""

    def __init__(self, workspaces: Workspaces) -> None:
        raise NotImplementedError

    async def execute(self, args: str = "", by: int = LOCAL, **kwargs: Any) -> Reply:
        """Open the workspace named in ``args`` for ``by``; a refusal is an error reply. Implements REQ-HARNESS-006."""
        raise NotImplementedError


@tool("merge", "Merge a workspace into the main checkout: /merge <name>")
@require(HookExecute)
class MergeCommand:
    """``/merge <name>``: merge the workspace for the run's change. Implements REQ-HARNESS-007."""

    def __init__(self, workspaces: Workspaces, backend: GitBackend) -> None:
        raise NotImplementedError

    async def execute(self, args: str = "", by: int = LOCAL, **kwargs: Any) -> Reply:
        """Merge the workspace named in ``args``; an error reply when the run has no change yet. Implements REQ-HARNESS-007."""
        raise NotImplementedError
