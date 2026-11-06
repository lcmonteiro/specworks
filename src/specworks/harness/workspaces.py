"""Workspaces: git worktrees on their own branches that peers work in, and the ``/workspace`` and ``/merge`` commands."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from chatinho import LOCAL, HookExecute, Reply, ReplyStatus, require, tool

from ..core.changes import Change
from ..core.errors import SpecworksError
from ..core.git import GitError, current_branch, git, git_text
from ..core.workspace import Module, Workspace
from ..workflow.merge import BranchMergeError, MergeResult, merge_branch

if TYPE_CHECKING:
    from .backend import GitBackend

WORKSPACES_DIR = ".specworks/workspaces"
MAIN = "main"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


# @req REQ-HARNESS-006
# @req REQ-HARNESS-007
class WorkspaceError(SpecworksError):
    """A workspace refused: a bad or unknown name, or a merge aborted on a conflict (``files``).

    Implements REQ-HARNESS-006, REQ-HARNESS-007.
    """

    def __init__(self, message: str, files: list[Path] | None = None) -> None:
        super().__init__(message)
        self.files: list[Path] = list(files or [])


# @req REQ-HARNESS-006
# @req REQ-HARNESS-007
class Workspaces:
    """Each peer's workspace (``main``, the main checkout, until it opens another). Implements REQ-HARNESS-006, REQ-HARNESS-007."""

    def __init__(self, ws: Workspace, module: Module) -> None:
        self.ws = ws
        self.module = module
        self.folder = ws.root / WORKSPACES_DIR
        self._of: dict[int, str] = {}  # peer id -> workspace name; a peer not in it is in main

    def path_of(self, peer: int) -> Path:
        """The folder of ``peer``'s workspace. Implements REQ-HARNESS-006."""
        name = self.name_of(peer)
        return self.ws.root if name == MAIN else self.folder / name

    def name_of(self, peer: int) -> str:
        """The name of ``peer``'s workspace. Implements REQ-HARNESS-006."""
        return self._of.get(peer, MAIN)

    def branch_of(self, name: str) -> str:
        """The branch of the workspace ``name``: ``<main branch>--<name>``. Implements REQ-HARNESS-006."""
        branch = current_branch(self.ws.root)
        if branch is None:
            raise WorkspaceError("the main checkout's HEAD is detached: switch to the change's branch first")
        return f"{branch}--{name}"

    def open(self, name: str, peer: int) -> Path:
        """Create (or reuse) the workspace ``name`` and make it ``peer``'s; ``main`` is the main checkout.

        Raises ``WorkspaceError`` for a name that is not lowercase letters, digits and hyphens. Implements REQ-HARNESS-006.
        """
        if name == MAIN:
            self._of.pop(peer, None)
            return self.ws.root
        if not NAME_RE.match(name):
            raise WorkspaceError(f"bad workspace name '{name}': use lowercase letters, digits and hyphens, starting with a letter or digit")
        path = self.folder / name
        if not path.is_dir():
            branch = self.branch_of(name)
            self.folder.mkdir(parents=True, exist_ok=True)
            ignore = self.folder / ".gitignore"
            if not ignore.exists():
                ignore.write_text("*\n", encoding="utf-8")  # the worktrees never show in the main checkout's status
            try:
                git(self.ws.root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}")
            except GitError:  # a new workspace: a new branch from the main checkout's commit
                git(self.ws.root, "worktree", "add", "-b", branch, str(path))
            else:  # its branch outlived its folder: check it out again
                git(self.ws.root, "worktree", "add", str(path), branch)
        self._of[peer] = name
        return path

    def merge(self, name: str, change: Change) -> MergeResult:
        """Merge the workspace's branch into the main checkout for ``change``, then remove it.

        Raises ``WorkspaceError`` for an unknown workspace (``no workspace '<name>'``) or a conflict (``files`` set).
        Implements REQ-HARNESS-007.
        """
        path = self.folder / name
        if name == MAIN or not NAME_RE.match(name) or not path.is_dir():
            raise WorkspaceError(f"no workspace '{name}'")
        if git_text(path, "status", "--porcelain").strip():
            raise WorkspaceError(f"workspace '{name}' has uncommitted changes: commit them in it before merging")
        branch = self.branch_of(name)
        try:
            result = merge_branch(self.ws, self.module, change, branch)
        except BranchMergeError as exc:  # aborted: the main checkout is as it was, and the workspace stays
            raise WorkspaceError(str(exc), exc.files) from None
        git(self.ws.root, "worktree", "remove", str(path))
        git(self.ws.root, "branch", "-D", branch)
        self._of = {peer: other for peer, other in self._of.items() if other != name}
        return result


def _error(exc: SpecworksError) -> Reply:
    """A refusal as the error reply to the peer that ran the command."""
    return Reply(str(exc), status=ReplyStatus.ERROR)


# @req REQ-HARNESS-006
@tool("workspace", "Work in a git workspace: /workspace <name>, or /workspace main")
@require(HookExecute)
class WorkspaceCommand:
    """``/workspace <name>``: the invoking peer's workspace becomes ``<name>``. Implements REQ-HARNESS-006."""

    def __init__(self, workspaces: Workspaces) -> None:
        self.workspaces = workspaces

    async def execute(self, args: str = "", by: int = LOCAL, **kwargs: Any) -> Reply:
        """Open the workspace named in ``args`` for ``by``; a refusal is an error reply. Implements REQ-HARNESS-006."""
        name = args.strip()
        if not name:
            return Reply("usage: /workspace <name>, or /workspace main", status=ReplyStatus.ERROR)
        try:
            path = self.workspaces.open(name, by)
        except SpecworksError as exc:
            return _error(exc)
        if name == MAIN:
            return Reply(f"now working in the main checkout ({path})")
        return Reply(f"now working in workspace {name} ({path}), branch {self.workspaces.branch_of(name)}")


# @req REQ-HARNESS-007
@tool("merge", "Merge a workspace into the main checkout: /merge <name>")
@require(HookExecute)
class MergeCommand:
    """``/merge <name>``: merge the workspace for the run's change. Implements REQ-HARNESS-007."""

    def __init__(self, workspaces: Workspaces, backend: GitBackend) -> None:
        self.workspaces = workspaces
        self.backend = backend

    async def execute(self, args: str = "", by: int = LOCAL, **kwargs: Any) -> Reply:
        """Merge the workspace named in ``args``; an error reply when the run has no change yet. Implements REQ-HARNESS-007."""
        name = args.strip()
        if not name:
            return Reply("usage: /merge <name>", status=ReplyStatus.ERROR)
        change = self.backend.change
        if change is None:
            return Reply("the run has no change yet: create it before merging a workspace", status=ReplyStatus.ERROR)
        try:
            result = self.workspaces.merge(name, change)
        except SpecworksError as exc:  # a conflict's message names the conflicting files
            return _error(exc)
        lines = [f"resolved {_rel(self.workspaces.ws, p)}" for p in result.resolved]
        lines.append(f"merged {result.branch} into the main checkout" if result.merged else f"{result.branch}: already up to date, nothing to merge")
        lines.append(f"workspace {name} removed")
        return Reply("\n".join(lines))


def _rel(ws: Workspace, path: Path) -> str:
    """``path`` relative to the workspace root, or as it is when it lies outside it."""
    try:
        return ws.rel(path)
    except ValueError:
        return path.as_posix()
