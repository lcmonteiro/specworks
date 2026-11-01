"""Running git: its output as bytes or text, and one error for a missing git or a failed command."""

import hashlib
import os
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from subprocess import run

from .errors import SpecworksError


class GitError(SpecworksError):
    """Raised when git is not installed or a git command fails (e.g. outside a repository)."""


class GitMissing(GitError):
    """Raised when git cannot be run (REQ-PROJ-017)."""


def git(cwd: Path, *args: str, stdin: bytes | None = None) -> bytes:
    try:
        proc = run(["git", *args], cwd=cwd, input=stdin, capture_output=True, check=False)
    except OSError as exc:
        raise GitMissing(f"cannot run git: {exc}") from None
    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout).decode("utf-8", "replace").strip()
        raise GitError(message or f"git {' '.join(args)} failed")
    return proc.stdout


def git_text(cwd: Path, *args: str) -> str:
    # git writes paths as UTF-8 whatever the platform; the locale's code page (on Windows)
    # would garble non-ASCII names into paths that do not exist.
    return git(cwd, *args).decode("utf-8", "surrogateescape")


@dataclass(frozen=True)
class Branch:
    """A change's branch and the branch it starts from, `None` when that is not known (REQ-PROJ-019)."""

    name: str
    started_from: str | None


# @req REQ-PROJ-017
def require_repo(path: Path) -> None:
    """Fail unless `path` is inside a git repository; runs git from the nearest existing parent.

    Raises `GitMissing` when git cannot be run, `GitError` ("not inside a git repository: run `git init` first")
    otherwise. Implements REQ-PROJ-017.
    """
    folder = path.resolve()
    while not folder.exists() and folder != folder.parent:
        folder = folder.parent
    try:
        git(folder, "rev-parse", "--git-dir")
    except GitMissing:
        raise
    except GitError:
        raise GitError(f"{path} is not inside a git repository: run `git init` first") from None


# @req REQ-PROJ-018
def branch_name(ref: str) -> str:
    """The branch for a change ref: `ref` with `:` replaced by `/`. Implements REQ-PROJ-018."""
    return ref.replace(":", "/")


# @req REQ-PROJ-018
# @req REQ-PROJ-019
def plan_branch(cwd: Path, name: str, base: str | None = None) -> Branch:
    """Check the branch can be created, without changing the repository.

    `base` is the base branch name (`origin/main` counts as `main`). Raises `GitError` for an existing branch or a
    detached HEAD. Implements REQ-PROJ-018, REQ-PROJ-019.
    """
    try:
        current = git_text(cwd, "symbolic-ref", "--short", "HEAD").strip()  # also works before the first commit
    except GitMissing:
        raise
    except GitError:
        raise GitError("HEAD is detached: switch to a branch first") from None
    try:
        git(cwd, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}")
    except GitError:
        pass
    else:
        raise GitError(f"branch '{name}' already exists")
    on_base = base is not None and current == base.removeprefix("origin/")
    return Branch(name, None if base is None or on_base else current)


# @req REQ-PROJ-018
# @req REQ-PROJ-019
def create_branch(cwd: Path, branch: Branch) -> None:
    """Create the branch and switch to it, carrying the working tree over. Implements REQ-PROJ-018, REQ-PROJ-019."""
    git(cwd, "checkout", "-b", branch.name)


# @req REQ-CLI-015
def current_branch(cwd: Path) -> str | None:
    """The branch HEAD is on (`symbolic-ref --short HEAD`), `None` on a detached HEAD. Implements REQ-CLI-015."""
    try:
        return git_text(cwd, "symbolic-ref", "--short", "HEAD").strip()  # also works before the first commit
    except GitMissing:
        raise
    except GitError:
        return None


DELETED = "deleted"  # the record's value for a dirty file that no longer exists (REQ-PROJ-023)
DETACHED = "cannot commit on a detached HEAD; switch to a branch first"


def _content_hash(path: Path) -> str | None:
    """SHA-256 hex of a file's bytes (a symlink's target text), `deleted` when it is gone, None for a folder (a submodule)."""
    if path.is_symlink():
        return hashlib.sha256(os.readlink(path).encode("utf-8", "surrogateescape")).hexdigest()
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return None if path.exists() else DELETED


# @req REQ-PROJ-023
# @req REQ-PROJ-024
def dirty_files(root: Path) -> dict[str, str]:
    """The staged, unstaged and untracked (not ignored) files under `root`, by path relative to it (POSIX).

    Each maps to the SHA-256 hex of its content, or `deleted` when it no longer exists. Raises `GitError` outside a
    repository. Implements REQ-PROJ-023, REQ-PROJ-024.
    """
    # Porcelain paths are relative to the repository's top; the workspace root can be below it.
    prefix = git_text(root, "rev-parse", "--show-prefix").strip()
    out = git_text(root, "-c", "core.quotepath=off", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", ".")
    fields = out.split("\0")
    paths: set[str] = set()
    i = 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if len(entry) < 4:
            continue
        paths.add(entry[3:])
        if "R" in entry[:2] or "C" in entry[:2]:
            paths.add(fields[i])  # a rename's or copy's source follows its new path
            i += 1
    found: dict[str, str] = {}
    for path in sorted(paths):
        if not path.startswith(prefix):
            continue  # the source of a rename from outside the workspace
        rel = path[len(prefix) :]
        if (digest := _content_hash(root / rel)) is not None:
            found[rel] = digest
    return found


# @req REQ-PROJ-024
def commit(root: Path, paths: Sequence[str], message: str) -> str:
    """Stage exactly `paths` (relative to `root`, deletions included) and commit them with `message`; return the short hash.

    The message goes to git on stdin. Raises `GitError` ("cannot commit on a detached HEAD; switch to a branch first")
    before staging anything on a detached HEAD. Never pushes. Implements REQ-PROJ-024.
    """
    try:
        git(root, "symbolic-ref", "-q", "HEAD")  # also works before the first commit
    except GitMissing:
        raise
    except GitError:
        raise GitError(DETACHED) from None
    pathspec = b"".join(p.encode("utf-8", "surrogateescape") + b"\0" for p in paths)
    existing = b"".join(p.encode("utf-8", "surrogateescape") + b"\0" for p in paths if os.path.lexists(root / p))
    if existing:  # new files must be known to git before a commit of only these paths
        git(root, "--literal-pathspecs", "add", "--pathspec-from-file=-", "--pathspec-file-nul", stdin=existing)
    # `commit -- <paths>` commits only these paths, as they are in the working tree (deletions included), and leaves
    # anything else already staged out of it. The paths go in a file, since stdin carries the message.
    fd, name = tempfile.mkstemp(prefix="specworks-pathspec-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(pathspec)
        git(
            root,
            "--literal-pathspecs",
            "commit",
            "-q",
            "--cleanup=whitespace",
            "-F",
            "-",
            f"--pathspec-from-file={name}",
            "--pathspec-file-nul",
            stdin=message.encode("utf-8"),
        )
    finally:
        os.unlink(name)
    return git_text(root, "rev-parse", "--short", "HEAD").strip()
