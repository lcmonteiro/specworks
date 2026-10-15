"""Run the project's own commands (``commands:`` in the config) from the right folder."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

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
