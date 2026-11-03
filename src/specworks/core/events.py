"""A change's event log: one JSON line per command that acted on it, kept git-ignored in the change's folder.

``events.jsonl`` holds the events, ``events.sent`` how many of its lines were already sent,
and a ``.gitignore`` there names both. Sending them is ``tools/langfuse.py``'s business.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from .changes import Change

EVENTS_FILE = "events.jsonl"
SENT_FILE = "events.sent"
IGNORE_FILE = ".gitignore"


# @req REQ-PROJ-030
def record_event(change: Change, enabled: bool, event: str, **fields: object) -> None:
    """Append one event line (``at`` in UTC, ``event``, the change's ``phase``, then ``fields``) to the change's log.

    Writes nothing when ``enabled`` is false; never raises. Implements REQ-PROJ-030.
    """
    if not enabled:
        return
    try:
        at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = json.dumps({"at": at, "event": event, "phase": change.phase, **fields}, ensure_ascii=False, default=str)
        with (change.path / EVENTS_FILE).open("a", encoding="utf-8") as log:
            log.write(line + "\n")  # one write in append mode, so two processes never interleave inside a line
        ignore = change.path / IGNORE_FILE
        if not ignore.exists():
            ignore.write_text(f"{EVENTS_FILE}\n{SENT_FILE}\n", encoding="utf-8")
    except Exception:  # noqa: BLE001 - the log must never fail the command that records the event
        return


# @req REQ-INTEG-009
def read_unsent(change: Change) -> tuple[int, list[dict]]:
    """The number of lines already sent, and the unsent events in order, each with its line number as ``line``.

    A line that is not a JSON object is skipped. Implements REQ-INTEG-009.
    """
    sent = _sent_count(change)
    log = change.path / EVENTS_FILE
    if not log.is_file():
        return sent, []
    events = []
    for number, text in enumerate(log.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if number <= sent:
            continue
        try:
            event = json.loads(text)
        except ValueError:
            event = None
        if isinstance(event, dict):  # a torn or hand-edited line is skipped, and still counted when sent
            events.append({**event, "line": number})
    return sent, events


# @req REQ-INTEG-009
def mark_sent(change: Change, count: int) -> None:
    """Add ``count`` to the change's ``events.sent``. Implements REQ-INTEG-009."""
    (change.path / SENT_FILE).write_text(f"{_sent_count(change) + count}\n", encoding="utf-8")


def _sent_count(change: Change) -> int:
    """The number in ``events.sent``; 0 when it is missing or not a number."""
    try:
        return max(int((change.path / SENT_FILE).read_text(encoding="utf-8").strip()), 0)
    except (OSError, ValueError):
        return 0


# @req REQ-PROJ-031
def trace_id(module_label: str, change: Change) -> str:
    """The change's stable trace ID: 32 hex characters from its module label, name and creation time. Implements REQ-PROJ-031."""
    return hashlib.sha256(f"{module_label}\n{change.name}\n{change.created}".encode()).hexdigest()[:32]


# @req REQ-PROJ-031
def session_id(ref: str) -> str:
    """The change's session ID: its ref. Implements REQ-PROJ-031."""
    return ref
