"""Running git: one place that calls it and decodes what it prints.

git writes paths as bytes (UTF-8 in practice, whatever the platform). Text output
is decoded as UTF-8 with ``surrogateescape``, so a name that is not valid UTF-8
still round-trips to the same file instead of crashing; ``fs_path`` turns a raw
path from ``-z`` output into a ``Path``.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .errors import SpecworksError


class GitError(SpecworksError):
    """Raised when git is missing or a git command fails."""


def git(cwd: Path, *args: str, input: bytes | None = None, ok_codes: tuple[int, ...] = (0,)) -> bytes:
    """The stdout of ``git <args>`` run in ``cwd``; GitError when git is missing or exits with another code."""
    try:
        proc = subprocess.run(["git", *args], cwd=cwd, input=input, capture_output=True, check=False)
    except OSError as exc:
        raise GitError(f"cannot run git: {exc}") from None
    if proc.returncode not in ok_codes:
        message = (proc.stderr or proc.stdout).decode("utf-8", "replace").strip()
        raise GitError(message or f"git {' '.join(args)} failed")
    return proc.stdout


def git_text(cwd: Path, *args: str) -> str:
    return git(cwd, *args).decode("utf-8", "surrogateescape")


def try_git(cwd: Path, *args: str) -> bytes | None:
    """Like ``git``, but None instead of an error (when the answer is only an optimisation)."""
    try:
        return git(cwd, *args)
    except GitError:
        return None


def fs_path(root: Path, raw: bytes) -> Path:
    """``root`` joined with a raw path from git's ``-z`` output."""
    return root / os.fsdecode(raw)


def split_z(output: bytes) -> list[bytes]:
    """The entries of NUL-separated (``-z``) output."""
    return [entry for entry in output.split(b"\0") if entry]
