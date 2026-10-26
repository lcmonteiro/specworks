"""Merging a half's branch into the current checkout for a change (in /specworks-build, the test half's worktree).

Git merges the branch; when the only conflicts are in the change's ``tasks.md`` and ``traceability.md``, they are
resolved (every tick kept, the trace regenerated) and the merge is committed. Anything else aborts the merge and
leaves the checkout as it was.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..core.changes import Change
from ..core.errors import SpecworksError
from ..core.workspace import Module, Workspace


class BranchMergeError(SpecworksError):
    """Raised when a branch cannot be merged for a change: refused before merging, or aborted on a conflict.

    ``files`` holds the conflicting files; it is empty when the merge was refused before it started (uncommitted
    changes, an unknown branch). Named apart from ``specworks.specs.merge.MergeError``, which close raises.
    Implements REQ-FLOW-015.
    """

    def __init__(self, message: str, files: list[Path] | None = None) -> None:
        super().__init__(message)
        self.files: list[Path] = list(files or [])


@dataclass(frozen=True)
class MergeResult:
    """A merged branch: ``merged`` is False only when git had nothing to merge; ``resolved`` lists the files resolved.

    Implements REQ-FLOW-015, REQ-CLI-010.
    """

    merged: bool
    branch: str
    resolved: list[Path]

    def to_dict(self, ws: Workspace) -> dict:
        """``merged``, ``branch`` and ``resolved`` (paths relative to the workspace root). Implements REQ-CLI-010."""
        raise NotImplementedError


def merge_ticks(ours: str, theirs: str) -> str | None:
    """``tasks.md`` with each line ticked when either side ticks it; ``None`` when a line differs in more than its box.

    Implements REQ-FLOW-015.
    """
    raise NotImplementedError


def merge_branch(ws: Workspace, module: Module, change: Change, branch: str) -> MergeResult:
    """Merge ``branch`` into the current checkout for ``change``, resolving its ``tasks.md`` and ``traceability.md``.

    Refuses a checkout with uncommitted changes or an unknown branch before merging; aborts the merge on any other
    conflict, or on a ``tasks.md`` line that differs in more than its box. ``module`` gives the change's ref for the
    regenerated trace. Raises ``BranchMergeError``, and ``GitError`` outside a git repository. Implements REQ-FLOW-015.
    """
    raise NotImplementedError
