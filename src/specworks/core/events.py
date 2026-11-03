"""A change's event log: one JSON line per command that acted on it, kept git-ignored in the change's folder.

``events.jsonl`` holds the events, ``events.sent`` how many of its lines were already sent,
and a ``.gitignore`` there names both. Sending them is ``tools/langfuse.py``'s business.
"""

from __future__ import annotations

from .changes import Change

EVENTS_FILE = "events.jsonl"
SENT_FILE = "events.sent"
IGNORE_FILE = ".gitignore"


def record_event(change: Change, enabled: bool, event: str, **fields: object) -> None:
    """Append one event line (``at`` in UTC, ``event``, the change's ``phase``, then ``fields``) to the change's log.

    Writes nothing when ``enabled`` is false; never raises. Implements REQ-PROJ-030.
    """
    raise NotImplementedError


def read_unsent(change: Change) -> tuple[int, list[dict]]:
    """The number of lines already sent, and the unsent events in order, each with its line number as ``line``.

    A line that is not a JSON object is skipped. Implements REQ-INTEG-009.
    """
    raise NotImplementedError


def mark_sent(change: Change, count: int) -> None:
    """Add ``count`` to the change's ``events.sent``. Implements REQ-INTEG-009."""
    raise NotImplementedError


def trace_id(module_label: str, change: Change) -> str:
    """The change's stable trace ID: 32 hex characters from its module label, name and creation time. Implements REQ-PROJ-031."""
    raise NotImplementedError


def session_id(ref: str) -> str:
    """The change's session ID: its ref. Implements REQ-PROJ-031."""
    raise NotImplementedError
