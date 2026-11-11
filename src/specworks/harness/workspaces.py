"""Workspaces: the main checkout the phase peers share, a git worktree for ``test``, a ``run`` operation, and ``/merge``."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from collections.abc import Set as AbstractSet
from pathlib import Path
from typing import TYPE_CHECKING, Any

from chatinho import LOCAL, HookExecute, Reply, ReplyStatus, require, tool
from chatinho.workspaces import GitWorktrees, Tree, Workspace, WorkspaceView, operation
from chatinho.workspaces.git import BRANCH_PREFIX, WORKTREES
from chatinho.workspaces.tree import run_git

from specworks.core.errors import SpecworksError
from specworks.core.git import git_text
from specworks.core.workspace import Workspace as SpecworksProject
from specworks.harness.confine import refuses, shell_env
from specworks.harness.peers import worktree_peers
from specworks.workflow.merge import BranchMergeError, merge_branch

if TYPE_CHECKING:
    from specworks.harness.backend import GitBackend

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


# @req REQ-HARNESS-008
class SpecworksWorkspace(Workspace):
    """chatinho's ``Workspace`` with a ``run`` operation, which agents get as ``ws_run``. Implements REQ-HARNESS-008."""

    @operation("Run a shell command in the workspace and return its output and exit code", writes=True)
    async def run(self, command: str) -> str:
        """Run ``command`` through the platform shell in the workspace's folder, with ``shell_env()``.

        Returns ``"exit code <n>\\n<output>"`` (stderr merged into stdout). Raises ``PermissionError`` for a ``git push``
        (nothing runs) and ``TimeoutError`` once it has run past ``RUN_TIMEOUT`` (it is killed). Implements REQ-HARNESS-008.
        """
        if refuses(command):
            raise PermissionError("git push is refused: only the user pushes")
        limit = RUN_TIMEOUT
        # Its own process group on POSIX, so a timeout stops the shell and every command it started.
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=self.tree.root,
            env=shell_env(),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=sys.platform != "win32",
        )
        try:
            out, _ = await asyncio.wait_for(process.communicate(), timeout=limit)
        except TimeoutError:
            await _kill(process)
            await process.wait()
            raise TimeoutError(f"command stopped after {limit:g} seconds") from None
        return f"exit code {process.returncode}\n{out.decode('utf-8', 'replace')}"


async def _kill(process: asyncio.subprocess.Process) -> None:
    """Stop ``process`` and every process it started: its process group on POSIX, its process tree on Windows."""
    if sys.platform != "win32":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:  # already gone
            pass
        return
    # Killing the shell alone (cmd.exe) leaves the command it started running; taskkill /T stops the whole tree.
    killer = await asyncio.create_subprocess_exec(  # pragma: no cover - Windows only
        "taskkill", "/F", "/T", "/PID", str(process.pid), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await killer.wait()  # pragma: no cover - Windows only
    if process.returncode is None:  # pragma: no cover - Windows only
        process.kill()


# @req REQ-HARNESS-006
class SpecworksWorktrees(GitWorktrees):
    """The provider: one main checkout every phase peer shares, and a worktree for each of ``worktrees``.

    Implements REQ-HARNESS-006.
    """

    def __init__(self, ws: SpecworksProject, worktrees: AbstractSet[str] | None = None) -> None:
        """Over the repository of ``ws`` (``repo=ws.root``), with ``SpecworksWorkspace`` as the owner's workspace.

        ``worktrees`` names the peers that get a worktree of their own; ``None`` means ``worktree_peers()``. Implements REQ-HARNESS-006.
        """
        super().__init__(ws.root, workspace=SpecworksWorkspace)
        self.ws = ws
        #: The names of the peers that work in a git worktree of their own; every other peer works in the main checkout.
        self.worktrees: frozenset[str] = worktree_peers() if worktrees is None else frozenset(worktrees)
        #: The main checkout, one tree (so one lock) for every peer that works in it; built once started.
        self._checkout: Tree | None = None

    async def provision(self, owner: str | None, name: str, create: bool = True) -> WorkspaceView:
        """``name``'s workspace for ``owner``: the main checkout for a name not in ``self.worktrees``, else its worktree.

        The main checkout is a ``SpecworksWorkspace`` when ``owner`` is a checkout peer too, a ``WorkspaceView`` otherwise.
        A worktree created now starts from the branch the checkout has now. Implements REQ-HARNESS-006.
        """
        if name in self.worktrees:
            top = await self._started()
            if create and not (top / WORKTREES / name / ".git").exists() and not await self._branch_exists(BRANCH_PREFIX + name):
                self.base = await self.current_branch()  # a new worktree starts where the checkout is now
            return await super().provision(owner, name, create)
        tree = await self._checkout_tree()
        writes = owner is not None and owner not in self.worktrees
        return (self.workspace if writes else self.view)(tree)

    async def _checkout_tree(self) -> Tree:
        """The main checkout's tree; its base is ``HEAD``, so its diff is the uncommitted work on whatever branch it is on."""
        top = await self._started()
        async with self._opening:
            if self._checkout is None:
                self._checkout = Tree(top, "checkout", await self.current_branch(), "HEAD", self.view, self._identity)
            return self._checkout

    async def current_branch(self) -> str:
        """The branch the main checkout has checked out, else its ``HEAD`` commit. Implements REQ-HARNESS-006."""
        top = await self._started()
        branch = (await run_git(top, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)).strip()
        return branch or (await run_git(top, "rev-parse", "HEAD")).strip()


# @req REQ-HARNESS-007
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
        name = args.strip()
        if by != LOCAL:
            return _error(f"only the user can merge: ask the user to run /merge {name or '<name>'}")
        if not name:
            return _error("usage: /merge <name>")
        change = self.backend.change
        if change is None:
            return _error("the run has no change yet: ask the peer working on the change to go on with it (such as @build go on with <change>), then merge")
        if name not in await self.provider.names():
            return _error(f"no workspace '{name}'")
        root = (await self.provider.provision(None, name, create=False)).tree.root
        if (await asyncio.to_thread(git_text, root, "status", "--porcelain")).strip():
            return _error(f"workspace '{name}' has uncommitted changes: commit them in it before merging")
        branch = BRANCH_PREFIX + name
        try:
            result = await asyncio.to_thread(merge_branch, self.backend.ws, self.backend.module, change, branch)
        except BranchMergeError as exc:  # aborted: the main checkout is as it was, and the workspace stays
            return _error(str(exc))
        await self.provider.drop(name)
        lines = [f"resolved {_rel(self.backend.ws, p)}" for p in result.resolved]
        lines.append(f"merged {branch} into the main checkout" if result.merged else f"{branch}: already up to date, nothing to merge")
        lines.append(f"workspace {name} removed")
        return Reply("\n".join(lines))


def _error(text: str) -> Reply:
    """A refusal, as the error reply to whoever ran the command."""
    return Reply(text, status=ReplyStatus.ERROR)


def _rel(ws: SpecworksProject, path: Path) -> str:
    """``path`` relative to the workspace root, or as it is when it lies outside it."""
    try:
        return ws.rel(path)
    except ValueError:
        return path.as_posix()
