"""Running git: its output as bytes or text, and one error for a missing git or a failed command."""

from dataclasses import dataclass
from pathlib import Path
from subprocess import run

from .errors import SpecworksError


class GitError(SpecworksError):
    """Raised when git is not installed or a git command fails (e.g. outside a repository)."""


def git(cwd: Path, *args: str) -> bytes:
    try:
        proc = run(["git", *args], cwd=cwd, capture_output=True, check=False)
    except OSError as exc:
        raise GitError(f"cannot run git: {exc}") from None
    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout).decode("utf-8", "replace").strip()
        raise GitError(message or f"git {' '.join(args)} failed")
    return proc.stdout


def git_text(cwd: Path, *args: str) -> str:
    # git writes paths as UTF-8 whatever the platform; the locale's code page (on Windows)
    # would garble non-ASCII names into paths that do not exist.
    return git(cwd, *args).decode("utf-8", "surrogateescape")


class GitMissing(GitError):
    """Raised when git cannot be run (REQ-PROJ-017)."""


@dataclass(frozen=True)
class Branch:
    """A change's branch and the branch it starts from, `None` when that is not known (REQ-PROJ-019)."""

    name: str
    started_from: str | None


def require_repo(path: Path) -> None:
    """Fail unless `path` is inside a git repository; runs git from the nearest existing parent.

    Raises `GitMissing` when git cannot be run, `GitError` ("not inside a git repository: run `git init` first")
    otherwise. Implements REQ-PROJ-017.
    """
    raise NotImplementedError


def branch_name(ref: str) -> str:
    """The branch for a change ref: `ref` with `:` replaced by `/`. Implements REQ-PROJ-018."""
    raise NotImplementedError


def plan_branch(cwd: Path, name: str, base: str | None = None) -> Branch:
    """Check the branch can be created, without changing the repository.

    `base` is the base branch name (`origin/main` counts as `main`). Raises `GitError` for an existing branch or a
    detached HEAD. Implements REQ-PROJ-018, REQ-PROJ-019.
    """
    raise NotImplementedError


def create_branch(cwd: Path, branch: Branch) -> None:
    """Create the branch and switch to it, carrying the working tree over. Implements REQ-PROJ-018, REQ-PROJ-019."""
    raise NotImplementedError
