"""
Telemetry in the CLI: recording a command's event, the state for `context`, the IDs for `status`,
sending after `commit`, and `specworks telemetry push`.
"""

from __future__ import annotations

import time

import typer

from specworks.cli.app import telemetry_app
from specworks.cli.output import ChangeOpt, JsonOpt, emit, fail, resolve_archived, resolve_change, workspace
from specworks.core.changes import Change, ChangeNotFound
from specworks.core.config import TelemetryConfig
from specworks.core.events import record_event, session_id, trace_id
from specworks.core.workspace import Module, Workspace
from specworks.tools.langfuse import SendResult, langfuse_settings, send_events


# @req REQ-CLI-017
def record(ws: Workspace, module: Module, change: Change, event: str, started: float, /, **fields: object) -> None:
    """
    Record ``event`` for ``change`` with ``ms`` since ``started`` (``time.monotonic()``) when the top level opted in.

    Implements REQ-CLI-017.
    """
    enabled = (ws.top.config.telemetry or TelemetryConfig()).langfuse  # only the top level's setting counts
    record_event(change, enabled, event, ms=int((time.monotonic() - started) * 1000), **fields)


# @req REQ-CLI-004
def telemetry_state(ws: Workspace) -> dict:
    """
    ``{"state", "host"}`` for `context`; never a key. Implements REQ-CLI-004.
    """
    settings = langfuse_settings(ws.top.config.telemetry)
    return {"state": settings.state, "host": settings.host}


# @req REQ-CLI-019
def telemetry_ids(module: Module, change: Change) -> dict:
    """
    ``{"traceId", "sessionId"}`` of ``change`` for `status`. Implements REQ-CLI-019.
    """
    return {"traceId": trace_id(module.label, change), "sessionId": session_id(module.qualify(change.name))}


def _send(ws: Workspace, module: Module, change: Change) -> SendResult:
    settings = langfuse_settings(ws.top.config.telemetry)
    return send_events(change, settings, trace_id(module.label, change), session_id(module.qualify(change.name)), module.label)


def _result_dict(result: SendResult) -> dict:
    return {"sent": result.sent, "queued": result.queued, "reason": result.reason}


# @req REQ-CLI-012
def send_after_commit(ws: Workspace, module: Module, change: Change) -> dict | None:
    """
    Send the change's unsent events after a commit: ``{"sent", "queued", "reason"}``, or None when telemetry is not on.

    Implements REQ-CLI-012.
    """
    if langfuse_settings(ws.top.config.telemetry).state != "on":
        return None
    return _result_dict(_send(ws, module, change))


# @req REQ-CLI-018
@telemetry_app.command("push")
def push(change: str = ChangeOpt, as_json: bool = JsonOpt) -> None:
    """
    Send a change's unsent events to Langfuse; exits 1 while events are still queued. Implements REQ-CLI-018.
    """
    ws = workspace(as_json)
    try:
        mod, ch = resolve_change(ws, change)
    except ChangeNotFound:
        mod, ch = resolve_archived(ws, change)
    settings = langfuse_settings(ws.top.config.telemetry)
    if settings.state == "off":
        fail("telemetry is off: set telemetry.langfuse to true in the top level's config", as_json)
    if settings.state == "keys missing":
        fail(f"telemetry keys missing: set {' and '.join(settings.missing)}", as_json)
    result = _send(ws, mod, ch)
    lines = [f"{mod.qualify(ch.name)}: sent {result.sent} event(s) to {settings.host}"]
    if result.queued:
        lines.append(f"{result.queued} event(s) still queued: {result.reason}")
    emit({"ref": mod.qualify(ch.name), **_result_dict(result)}, as_json, "\n".join(lines))
    if result.queued:
        raise typer.Exit(1)
