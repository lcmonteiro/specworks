"""Run the project's own commands (``commands:`` in the config) from the right folder.

Gates and validate run the same commands again and again on the same code (each
skill checks the previous phase's gate, then its own). ``cached_run`` reuses the
result of a run on an identical working tree: same command and folder, same
``HEAD``, same uncommitted and untracked files. The workflow folders
(``<dir>/``: specs, tasks, review.md) are left out, since writing them does not
change what the commands see. The cache lives inside ``.git/``; without git, or
with ``SPECWORKS_RUN_CACHE=0``, every run is real.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .errors import SpecworksError
from .workspace import Module, Workspace

TAIL_LINES = 40


class CommandError(SpecworksError):
    """Raised when a command is not configured."""


@dataclass
class RunResult:
    key: str
    command: str
    cwd: str
    exit_code: int
    output: str
    cached_at: str = ""  # when the reused run happened; empty for a fresh run

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    def tail(self, lines: int = TAIL_LINES) -> list[str]:
        return self.output.rstrip().splitlines()[-lines:]


def run_command(ws: Workspace, module: Module, key: str, capture: bool = True) -> RunResult:
    """Run ``commands.<key>`` (merged top level -> module) in the module's folder, through the shell."""
    command = ws.commands(module).get(key)
    if not command:
        where = ws.rel(module.config.config_path)
        raise CommandError(f"no '{key}' command configured; add it under commands: in {where} (e.g. test: uv run pytest)")
    proc = subprocess.run(
        command,
        shell=True,
        cwd=module.root,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )
    return RunResult(key=key, command=command, cwd=ws.rel(module.root), exit_code=proc.returncode, output=proc.stdout or "")


CACHE_FILE = "specworks-runs.json"
CACHE_SIZE = 50


def _git(cwd: Path, *args: str) -> bytes | None:
    try:
        proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=False)
    except OSError:
        return None
    return proc.stdout if proc.returncode == 0 else None


def _untracked_in_submodule(root: Path, excluded: list[str]) -> bool:
    """A submodule holds untracked files: git lists none of them, so the tree cannot be fingerprinted."""
    if not (root / ".gitmodules").is_file():
        return False
    status = _git(root, "status", "--porcelain=v2", "--ignore-submodules=none", "--", ".", *excluded)
    if status is None:
        return True
    # Changed entries are "1 <XY> <sub> ..."; <sub> is "S<C><M><U>" for a submodule, U meaning untracked content.
    return any(len(f := line.split(b" ")) > 2 and f[0] in (b"1", b"2") and f[2][:1] == b"S" and f[2][3:4] == b"U" for line in status.splitlines())


def tree_fingerprint(ws: Workspace, module: Module, command: str) -> tuple[str, Path] | None:
    """(digest of the command and the working tree, cache file), or None when git cannot tell."""
    top = _git(module.root, "rev-parse", "--show-toplevel")
    head = _git(module.root, "rev-parse", "HEAD")
    cache = _git(module.root, "rev-parse", "--git-path", CACHE_FILE)
    if top is None or head is None or cache is None:
        return None
    root = Path(top.decode().strip())
    excluded = [f":(exclude){(m.root / m.config.dir).resolve().relative_to(root).as_posix()}" for m in ws.modules()
                if (m.root / m.config.dir).resolve().is_relative_to(root)]
    # --submodule=diff: a dirty submodule shows its edits, not only "<commit>-dirty".
    diff = _git(root, "diff", "HEAD", "--binary", "--submodule=diff", "--", ".", *excluded)
    untracked = _git(root, "ls-files", "--others", "--exclude-standard", "-z", "--", ".", *excluded)
    if diff is None or untracked is None or _untracked_in_submodule(root, excluded):
        return None
    digest = hashlib.sha256("\0".join([command, str(module.root.resolve()), head.decode().strip()]).encode())
    digest.update(diff)
    for name in sorted(n for n in untracked.split(b"\0") if n):
        path = root / name.decode()
        digest.update(name + b"\0" + (hashlib.sha256(path.read_bytes()).digest() if path.is_file() else b""))
    return digest.hexdigest(), (module.root / cache.decode().strip()).resolve()


def _load(cache: Path) -> dict:
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def cached_run(ws: Workspace, module: Module, key: str) -> RunResult:
    """``run_command``, reusing the result of a run on an identical working tree when there is one."""
    command = ws.commands(module).get(key, "")
    found = tree_fingerprint(ws, module, command) if command and os.environ.get("SPECWORKS_RUN_CACHE", "1") != "0" else None
    if found is None:
        return run_command(ws, module, key)
    digest, cache = found
    runs = _load(cache)
    if isinstance(hit := runs.get(digest), dict):
        try:
            return RunResult(key, command, ws.rel(module.root), int(hit["exit_code"]), str(hit["output"]), cached_at=str(hit["at"]))
        except (KeyError, TypeError, ValueError):
            pass
    result = run_command(ws, module, key)
    runs[digest] = {"exit_code": result.exit_code, "output": "\n".join(result.tail()), "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        cache.write_text(json.dumps(dict(list(runs.items())[-CACHE_SIZE:]), indent=1), encoding="utf-8")
    except OSError:
        pass  # a cache that cannot be written only costs a rerun
    return result
