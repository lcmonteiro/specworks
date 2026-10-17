"""Running git: its output as bytes or text, and one error for a missing git or a failed command."""

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
