"""The git backend: the conversation kept in a git-ignored ``chat.jsonl`` in the run's change folder."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from chatinho import ChatMessage, HookForget, HookListen, ReplyStatus, backend, require

from ..core.changes import Change, list_changes
from ..core.events import EVENTS_FILE, IGNORE_FILE, SENT_FILE, ensure_ignored
from ..core.workspace import Module, Workspace

CHAT_FILE = "chat.jsonl"
#: Files a change's signature leaves out: the backend's own log, the telemetry log every change command appends to,
#: and the ``.gitignore`` a first logged event creates.
IGNORED = frozenset({CHAT_FILE, EVENTS_FILE, SENT_FILE, IGNORE_FILE})

logger = logging.getLogger(__name__)


# @req REQ-HARNESS-009
def to_line(msg: ChatMessage) -> dict[str, Any]:
    """``msg`` as a ``chat.jsonl`` line: ``id``, ``from``, ``to``, ``replyTo``, ``status``, ``text``, ``at``; never its credentials.

    Implements REQ-HARNESS-009.
    """
    return {
        "id": str(msg.id),
        "from": msg.frm,
        "to": msg.to,
        "replyTo": None if msg.reply_to is None else str(msg.reply_to),
        "status": ReplyStatus(msg.status).value,
        "text": msg.text,
        "at": msg.timestamp.isoformat(),
    }


# @req REQ-HARNESS-009
def signature(folder: Path) -> int:
    """The newest ``st_mtime_ns`` of any file in ``folder`` except ``chat.jsonl``, ``events.jsonl``, ``events.sent`` and ``.gitignore``.

    ``0`` for an empty or unreadable folder.

    Implements REQ-HARNESS-009.
    """
    newest = 0
    try:
        for path in folder.rglob("*"):
            if path.name not in IGNORED and path.is_file():
                newest = max(newest, path.stat().st_mtime_ns)
    except OSError:
        return 0
    return newest


# @req REQ-HARNESS-009
@backend("git")
@require(HookListen)
@require(HookForget)
class GitBackend:
    """Appends every message to the run's change's ``chat.jsonl``, holding them until the run has a change.

    Implements REQ-HARNESS-009.
    """

    change: Change | None

    def __init__(self, ws: Workspace, module: Module) -> None:
        """A backend with no change yet: the run's change is found from what the run does. Implements REQ-HARNESS-009."""
        self.ws = ws
        self.module = module
        #: The run's change: ``None`` until it is found.
        self.change = None
        #: Lines not written yet: all of them while the run has no change, and any whose write failed.
        self._held: list[dict[str, Any]] = []
        #: The active changes at start, each with its folder's signature; the first one new or changed is the run's.
        self._snapshot: dict[str, int] = {c.name: signature(c.path) for c in self._active()}

    def _active(self) -> list[Change]:
        """The module's active changes, by name; none when they cannot be read."""
        try:
            return sorted(list_changes(self.module.config), key=lambda c: c.name)
        except Exception:  # noqa: BLE001 - a broken change folder must not stop the chat
            logger.warning("cannot list the changes", exc_info=True)
            return []

    def _find_change(self) -> None:
        """Make the first active change, by name, created or changed since the start the run's change."""
        for change in self._active():
            if self._snapshot.get(change.name) != signature(change.path):
                self.change = change
                return

    def _flush(self) -> None:
        """Append the held lines to the change's ``chat.jsonl``, in order; on a failure they stay held."""
        if self.change is None or not self._held:
            return
        try:
            text = "".join(json.dumps(line, ensure_ascii=False) + "\n" for line in self._held)
            with (self.change.path / CHAT_FILE).open("a", encoding="utf-8") as log:
                log.write(text)
        except OSError as exc:
            logger.warning("cannot write %s: %s", CHAT_FILE, type(exc).__name__)
            return
        self._held.clear()
        ensure_ignored(self.change.path, (CHAT_FILE,))

    async def listen(self, msg: ChatMessage) -> None:
        """Append ``msg`` (or hold it while the run has no change); a write failure is logged and ignored. Implements REQ-HARNESS-009."""
        self._held.append(to_line(msg))
        if self.change is None:
            self._find_change()
        self._flush()

    async def forget(self, before: datetime | None = None) -> int:
        """Drop held lines (the file is kept); how many were dropped. Implements REQ-HARNESS-009."""
        kept = [] if before is None else [line for line in self._held if datetime.fromisoformat(line["at"]) >= before]
        dropped = len(self._held) - len(kept)
        self._held = kept
        return dropped
