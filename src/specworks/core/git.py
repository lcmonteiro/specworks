"""Running git: its output as bytes or text, and one error for a missing git or a failed command."""

from dataclasses import dataclass
from pathlib import Path
from subprocess import run

from .errors import SpecworksError


class GitError(SpecworksError):
    """Raised when git is not installed or a git command fails (e.g. outside a repository)."""


class GitMissing(GitError):
    """Raised when git cannot be run (REQ-PROJ-017)."""


def git(cwd: Path, *args: str) -> bytes:
    try:
        proc = run(["git", *args], cwd=cwd, capture_output=True, check=False)
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
