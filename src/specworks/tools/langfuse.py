"""The Langfuse client: telemetry settings from the config and the environment, and sending a change's unsent events.

Only the ``SPECWORKS_LANGFUSE_*`` variables are read, never the plain ``LANGFUSE_*`` ones, and the keys
are never written, printed or put in an error. Sending uses the public ingestion API with the standard library only.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal

from ..core.changes import Change
from ..core.config import TelemetryConfig
from ..core.events import mark_sent, read_unsent

DEFAULT_HOST = "https://cloud.langfuse.com"
TIMEOUT = 5.0  # seconds per request
BATCH_SIZE = 100  # events per ingestion request
ENV_PUBLIC_KEY = "SPECWORKS_LANGFUSE_PUBLIC_KEY"
ENV_SECRET_KEY = "SPECWORKS_LANGFUSE_SECRET_KEY"
ENV_HOST = "SPECWORKS_LANGFUSE_HOST"


@dataclass(frozen=True)
class LangfuseSettings:
    """Whether telemetry is ``on``, opted in with ``keys missing`` (named in ``missing``), or ``off``; the keys stay out of ``repr``.

    Implements REQ-INTEG-008.
    """

    state: Literal["on", "keys missing", "off"]
    host: str
    missing: tuple[str, ...] = ()
    public_key: str = field(default="", repr=False)
    secret_key: str = field(default="", repr=False)


# @req REQ-INTEG-008
def langfuse_settings(config: TelemetryConfig | None, env: Mapping[str, str] | None = None) -> LangfuseSettings:
    """The telemetry settings from the top level's ``telemetry`` block and ``env`` (``os.environ`` when None).

    Implements REQ-INTEG-008.
    """
    env = os.environ if env is None else env
    config = config or TelemetryConfig()
    host = env.get(ENV_HOST) or config.host or DEFAULT_HOST  # never the plain LANGFUSE_* variables
    if not config.langfuse:
        return LangfuseSettings("off", host)
    public_key, secret_key = env.get(ENV_PUBLIC_KEY, ""), env.get(ENV_SECRET_KEY, "")
    missing = tuple(name for name, value in ((ENV_PUBLIC_KEY, public_key), (ENV_SECRET_KEY, secret_key)) if not value)
    if missing:
        return LangfuseSettings("keys missing", host, missing)
    return LangfuseSettings("on", host, public_key=public_key, secret_key=secret_key)


@dataclass(frozen=True)
class SendResult:
    """How many events were sent, how many are still queued, and why not all were sent (None when they were).

    Implements REQ-INTEG-009.
    """

    sent: int
    queued: int
    reason: str | None


# @req REQ-INTEG-009
def send_events(change: Change, settings: LangfuseSettings, trace: str, session: str, module_label: str) -> SendResult:
    """Send the change's unsent events to Langfuse in batches, marking each accepted batch sent.

    Stops at the first failed batch; never raises for a network or server failure. Implements REQ-INTEG-009.
    """
    done, events = read_unsent(change)
    if not events:
        return SendResult(0, 0, None)
    if settings.state != "on":
        return SendResult(0, len(events), f"telemetry is {settings.state}")
    url = settings.host.rstrip("/") + "/api/public/ingestion"
    token = base64.b64encode(f"{settings.public_key}:{settings.secret_key}".encode()).decode("ascii")
    sent = 0
    for start in range(0, len(events), BATCH_SIZE):
        batch = events[start : start + BATCH_SIZE]
        body = {"batch": [_trace_item(trace, session, module_label, batch[0]), *(_span_item(trace, event) for event in batch)]}
        if reason := _post(url, token, body):
            return SendResult(sent, len(events) - sent, reason)
        last = batch[-1]["line"]
        mark_sent(change, last - done)  # skipped lines before ``last`` count as sent too
        done = last
        sent += len(batch)
    return SendResult(sent, 0, None)


def _post(url: str, token: str, body: dict) -> str | None:
    """POST ``body`` as JSON; None when the server accepts it (2xx), else a reason that never holds the keys."""
    where = urllib.parse.urlsplit(url).netloc or url
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False, default=str).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Basic {token}"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:  # noqa: S310 - only the configured Langfuse host
            status = response.status
    except urllib.error.HTTPError as exc:
        return f"Langfuse answered {exc.code}"
    except (urllib.error.URLError, OSError, ValueError) as exc:
        cause = exc.reason if isinstance(exc, urllib.error.URLError) else exc
        if isinstance(cause, TimeoutError):
            return f"no answer from {where} within {TIMEOUT:g} s: timed out"
        return f"could not reach {where}: {type(cause).__name__}"
    return None if 200 <= status < 300 else f"Langfuse answered {status}"


def _trace_item(trace: str, session: str, module_label: str, first: dict) -> dict:
    """The ``trace-create`` item: the change's trace, named and grouped by its ref."""
    body = {"id": trace, "name": session, "sessionId": session, "metadata": {"module": module_label}}
    return {"id": str(uuid.uuid4()), "type": "trace-create", "timestamp": _now(), "body": body}


def _span_item(trace: str, event: dict) -> dict:
    """A ``span-create`` item for one event line, its ID stable so a resend updates the same span."""
    at = str(event.get("at", ""))
    metadata = {key: value for key, value in event.items() if key not in ("at", "event", "line")}
    body = {
        "id": f"{trace}-{event['line']}",
        "traceId": trace,
        "name": str(event.get("event", "")),
        "startTime": _start(at, event.get("ms")),
        "endTime": at,
        "metadata": metadata,
    }
    return {"id": str(uuid.uuid4()), "type": "span-create", "timestamp": at or _now(), "body": body}


def _start(at: str, ms: object) -> str:
    """``at`` minus ``ms`` milliseconds, in UTC; ``at`` itself when either is not usable."""
    try:
        end = datetime.fromisoformat(at)
    except ValueError:
        return at
    if not isinstance(ms, int) or isinstance(ms, bool) or ms <= 0:
        return at
    start = (end - timedelta(milliseconds=ms)).astimezone(UTC)
    return start.strftime("%Y-%m-%dT%H:%M:%S.") + f"{start.microsecond // 1000:03d}Z"


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
