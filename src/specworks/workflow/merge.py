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
from ..core.git import GitError, git, git_text, require_repo
from ..core.workspace import Module, Workspace
from ..specs.tasks import TASK_RE, TASKS_FILE
from ..specs.trace import Analysis, to_markdown, write_traceability

TRACE_FILE = "traceability.md"


# @req REQ-FLOW-015
class BranchMergeError(SpecworksError):
    """Raised when a branch cannot be merged for a change: refused before merging, or aborted on a conflict.

    ``files`` holds the conflicting files; it is empty when the merge was refused before it started (uncommitted
    changes, an unknown branch). Named apart from ``specworks.specs.merge.MergeError``, which close raises.
    Implements REQ-FLOW-015.
    """

    def __init__(self, message: str, files: list[Path] | None = None) -> None:
        super().__init__(message)
        self.files: list[Path] = list(files or [])


# @req REQ-FLOW-015
@dataclass(frozen=True)
class MergeResult:
    """A merged branch: ``merged`` is False only when git had nothing to merge; ``resolved`` lists the files resolved.

    Implements REQ-FLOW-015, REQ-CLI-010.
    """

    merged: bool
    branch: str
    resolved: list[Path]

    # @req REQ-CLI-010
    def to_dict(self, ws: Workspace) -> dict:
        """``merged``, ``branch`` and ``resolved`` (paths relative to the workspace root). Implements REQ-CLI-010."""
        return {"merged": self.merged, "branch": self.branch, "resolved": [ws.rel(p) for p in self.resolved]}


def _box(line: str) -> tuple[str, bool]:
    """The line without its ending and with its task box emptied, and whether that box was ticked."""
    line = line.rstrip("\r\n")
    match = TASK_RE.match(line)
    if match is None or match.group("mark").strip().lower() not in ("", "x"):
        return line, False
    ticked = match.group("mark").strip().lower() == "x"
    return f"{match.group('lead')} {line[match.end('mark') :]}", ticked


# @req REQ-FLOW-015
def merge_ticks(ours: str, theirs: str) -> str | None:
    """``tasks.md`` with each line ticked when either side ticks it; ``None`` when a line differs in more than its box.

    Each line keeps the ours side's line ending. Implements REQ-FLOW-015.
    """
    our_lines, their_lines = ours.splitlines(keepends=True), theirs.splitlines(keepends=True)
    if len(our_lines) != len(their_lines):
        return None
    out = []
    for mine, other in zip(our_lines, their_lines, strict=True):
        (bare, mine_ticked), (other_bare, other_ticked) = _box(mine), _box(other)
        if bare != other_bare:
            return None
        if other_ticked and not mine_ticked:
            match = TASK_RE.match(mine.rstrip("\r\n"))
            assert match is not None  # _box found a task box on this line
            mine = f"{mine[: match.start('mark')]}x{mine[match.end('mark') :]}"
        out.append(mine)
    return "".join(out)


# @req REQ-FLOW-015
def merge_branch(ws: Workspace, module: Module, change: Change, branch: str) -> MergeResult:
    """Merge ``branch`` into the current checkout for ``change``, resolving its ``tasks.md`` and ``traceability.md``.

    Refuses a checkout with uncommitted changes or an unknown branch before merging; aborts the merge on any other
    conflict, or on a ``tasks.md`` line that differs in more than its box. ``module`` gives the change's ref for the
    regenerated trace. Raises ``BranchMergeError``, and ``GitError`` outside a git repository. Implements REQ-FLOW-015.
    """
    cwd = ws.root
    require_repo(cwd)
    if git_text(cwd, "status", "--porcelain").strip():
        raise BranchMergeError("the checkout has uncommitted changes: commit or stash them before merging")
    try:
        git(cwd, "rev-parse", "--verify", "--quiet", f"{branch}^{{commit}}")
    except GitError:
        raise BranchMergeError(f"branch '{branch}' does not exist") from None
    top = Path(git_text(cwd, "rev-parse", "--show-toplevel").strip())
    head = git_text(cwd, "rev-parse", "HEAD").strip()
    try:
        git(cwd, "merge", "--no-ff", "--no-edit", branch)
    except GitError as exc:
        conflicts = [top / p for p in git_text(cwd, "diff", "--name-only", "--diff-filter=U", "-z").split("\0") if p]
        if not conflicts:
            _abort(cwd)
            raise BranchMergeError(f"git could not merge '{branch}': {exc}") from None
        try:
            resolved = _resolve(ws, module, change, top, conflicts)
            git(cwd, "add", "--", *(str(p) for p in resolved))
            git(cwd, "commit", "--no-edit")
        except BaseException:
            _abort(cwd)
            raise
        return MergeResult(True, branch, resolved)
    return MergeResult(git_text(cwd, "rev-parse", "HEAD").strip() != head, branch, [])


def _abort(cwd: Path) -> None:
    """Abort the merge in progress, if any, restoring the checkout as it was before it."""
    try:
        git(cwd, "rev-parse", "--verify", "--quiet", "MERGE_HEAD")
    except GitError:
        return
    git(cwd, "merge", "--abort")


def _rel(ws: Workspace, path: Path) -> str:
    try:
        return ws.rel(path)
    except ValueError:  # a conflicting file of the repository outside the workspace
        return path.as_posix()


def _resolve(ws: Workspace, module: Module, change: Change, top: Path, conflicts: list[Path]) -> list[Path]:
    """Write the resolved ``tasks.md`` and ``traceability.md``; raise ``BranchMergeError`` on any other conflict."""
    tasks, trace = (change.path / TASKS_FILE).resolve(), (change.path / TRACE_FILE).resolve()
    others = [p for p in conflicts if p.resolve() not in (tasks, trace)]
    if others:
        raise BranchMergeError(f"merge aborted: conflicts in {', '.join(_rel(ws, p) for p in others)}", others)
    resolved = []
    if any(p.resolve() == tasks for p in conflicts):
        name = tasks.relative_to(top.resolve()).as_posix()
        try:
            ours, theirs = (git(top, "show", f":{stage}:{name}").decode("utf-8") for stage in (2, 3))
            merged = merge_ticks(ours, theirs)
        except (GitError, UnicodeDecodeError):  # a side deleted it, or it is not text
            merged = None
        if merged is None:
            raise BranchMergeError(f"merge aborted: {_rel(ws, tasks)} differs between the sides in more than its ticks", [tasks])
        tasks.write_text(merged, encoding="utf-8", newline="")
        resolved.append(tasks)
    if any(p.resolve() == trace for p in conflicts):
        analysis = Analysis(ws, change)
        resolved.append(write_traceability(change, to_markdown(module.qualify(change.name), analysis.rows, analysis.gaps)).resolve())
    return resolved
