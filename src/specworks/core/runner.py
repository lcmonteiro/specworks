"""Run the project's own commands (``commands:`` in the config) from the right folder.

Gates and validate run the same commands again and again on the same code (each
skill checks the previous phase's gate, then its own). ``cached_run`` reuses the
result of a run on an identical working tree: same command and folder, same
``HEAD``, same uncommitted and untracked files. The workflow folders
(``.specworks/``: specs, tasks, review.md) are left out, since writing them does not
change what the commands see. Every real run is recorded, ``specworks run``'s too,
so the latest run on a tree is the one reused: after fixing something the
fingerprint cannot see (a git-ignored file, a service), ``specworks run`` updates
it. The cache lives inside ``.git/``; without git, or with ``SPECWORKS_RUN_CACHE=0``,
every run is real.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .config import COMMAND_KEYS
from .errors import SpecworksError
from .git import GitError, git, git_text
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


# @req REQ-PROJ-013
def run_command(ws: Workspace, module: Module, key: str, capture: bool = True) -> RunResult:
    """Run ``commands.<key>`` (merged top level -> module) in the module's folder, through the shell."""
    if key not in COMMAND_KEYS:  # the config refuses any other key, so don't suggest adding it there
        raise CommandError(f"unknown command '{key}'; use one of {', '.join(COMMAND_KEYS)}")
    command = ws.commands(module).get(key)
    if not command:
        where = ws.rel(module.config.config_path)
        raise CommandError(f"no '{key}' command configured; add it under commands: in {where} (e.g. {key}: <command>)")
    proc = subprocess.run(
        command,
        shell=True,
        cwd=module.root,
        text=True,
        errors="replace",  # a tool's output may be in any encoding; a stray byte must not crash the gate
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )
    return RunResult(key=key, command=command, cwd=ws.rel(module.root), exit_code=proc.returncode, output=proc.stdout or "")


CACHE_FILE = "specworks-runs.json"
CACHE_SIZE = 50


def _untracked_in_submodule(root: Path, excluded: list[str]) -> bool:
    """A submodule holds untracked files: git lists none of them, so the tree cannot be fingerprinted."""
    if not (root / ".gitmodules").is_file():
        return False
    status = git(root, "status", "--porcelain=v2", "--ignore-submodules=none", "--", ".", *excluded)
    # Changed entries are "1 <XY> <sub> ..."; <sub> is "S<C><M><U>" for a submodule, U meaning untracked content.
    return any(len(f := line.split(b" ")) > 2 and f[0] in (b"1", b"2") and f[2][:1] == b"S" and f[2][3:4] == b"U" for line in status.splitlines())


# @req REQ-PROJ-014
def tree_fingerprint(ws: Workspace, module: Module, command: str) -> tuple[str, Path] | None:
    """(digest of the command and the working tree, cache file), or None when git cannot tell or an untracked file cannot be read."""
    try:
        root = Path(git_text(module.root, "rev-parse", "--show-toplevel").strip())
        head = git_text(module.root, "rev-parse", "HEAD").strip()
        cache = git_text(module.root, "rev-parse", "--git-path", CACHE_FILE).strip()
        excluded = [f":(exclude){(m.root / m.config.dir).resolve().relative_to(root).as_posix()}" for m in ws.modules()
                    if (m.root / m.config.dir).resolve().is_relative_to(root)]
        # --submodule=diff: a dirty submodule shows its edits, not only "<commit>-dirty".
        diff = git(root, "diff", "HEAD", "--binary", "--submodule=diff", "--", ".", *excluded)
        untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z", "--", ".", *excluded)
        if _untracked_in_submodule(root, excluded):
            return None
    except GitError:
        return None
    digest = hashlib.sha256("\0".join([command, str(module.root.resolve()), head]).encode())
    digest.update(diff)
    for name in sorted(n for n in untracked.split(b"\0") if n):
        path = root / os.fsdecode(name)  # the bytes git reports, whatever their encoding
        try:
            content = hashlib.sha256(path.read_bytes()).digest() if path.is_file() else b""
        except OSError:
            return None  # its content cannot be seen, so no earlier result may be reused
        digest.update(name + b"\0" + content)
    return digest.hexdigest(), (module.root / cache).resolve()


def _load(cache: Path) -> dict:
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


# @req REQ-PROJ-014
def cached_run(ws: Workspace, module: Module, key: str, reuse: bool = True, capture: bool = True) -> RunResult:
    """``run_command``, reusing the result of a run on an identical working tree when there is one.

    ``reuse=False`` always runs, and records the result for the next caller on this tree.
    """
    command = ws.commands(module).get(key, "")
    found = tree_fingerprint(ws, module, command) if command and os.environ.get("SPECWORKS_RUN_CACHE", "1") != "0" else None
    if found is None:
        return run_command(ws, module, key, capture)
    digest, cache = found
    runs = _load(cache)
    if reuse and isinstance(hit := runs.get(digest), dict):
        try:
            return RunResult(key, command, ws.rel(module.root), int(hit["exit_code"]), str(hit["output"]), cached_at=str(hit["at"]))
        except (KeyError, TypeError, ValueError):
            pass
    result = run_command(ws, module, key, capture)
    output = "\n".join(result.tail()) if capture else "(output was shown in the terminal, not kept)"
    runs.pop(digest, None)  # re-inserted last: the newest run is the last one evicted
    runs[digest] = {"exit_code": result.exit_code, "output": output, "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        cache.write_text(json.dumps(dict(list(runs.items())[-CACHE_SIZE:]), indent=1), encoding="utf-8")
    except OSError:
        pass  # a cache that cannot be written only costs a rerun
    return result
