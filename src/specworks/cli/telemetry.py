"""Telemetry in the CLI: recording a command's event, the state for `context`, the IDs for `status`,
sending after `commit`, and `specworks telemetry push`."""

from __future__ import annotations

from ..core.changes import Change
from ..core.workspace import Module, Workspace
from .app import telemetry_app
from .output import ChangeOpt, JsonOpt


def record(ws: Workspace, module: Module, change: Change, event: str, started: float, **fields: object) -> None:
    """Record ``event`` for ``change`` with ``ms`` since ``started`` (``time.monotonic()``) when the top level opted in.

    Implements REQ-CLI-017.
    """
    raise NotImplementedError


def telemetry_state(ws: Workspace) -> dict:
    """``{"state", "host"}`` for `context`; never a key. Implements REQ-CLI-004."""
    raise NotImplementedError


def telemetry_ids(module: Module, change: Change) -> dict:
    """``{"traceId", "sessionId"}`` of ``change`` for `status`. Implements REQ-CLI-019."""
    raise NotImplementedError


def send_after_commit(ws: Workspace, module: Module, change: Change) -> dict | None:
    """Send the change's unsent events after a commit: ``{"sent", "queued", "reason"}``, or None when telemetry is not on.

    Implements REQ-CLI-012.
    """
    raise NotImplementedError


@telemetry_app.command("push")
def push(change: str = ChangeOpt, as_json: bool = JsonOpt) -> None:
    """Send a change's unsent events to Langfuse; exits 1 while events are still queued. Implements REQ-CLI-018."""
    raise NotImplementedError
