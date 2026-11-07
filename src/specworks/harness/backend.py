"""The git backend: the conversation kept in a git-ignored ``chat.jsonl`` in the run's change folder."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from chatinho import ChatMessage, HookForget, HookListen, HookLoad, MessageID, ReplyStatus, backend, require

from ..core.changes import Change, list_changes
from ..core.events import ensure_ignored
from ..core.workspace import Module, Workspace

CHAT_FILE = "chat.jsonl"

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
def from_line(line: dict[str, Any]) -> ChatMessage:
    """The message a ``chat.jsonl`` line holds. Implements REQ-HARNESS-009."""
    return ChatMessage(
        id=MessageID.parse(str(line["id"])),
        text=str(line["text"]),
        frm=int(line["from"]),
        to=None if line.get("to") is None else int(line["to"]),
        reply_to=MessageID.parse(line.get("replyTo")),
        timestamp=datetime.fromisoformat(line["at"]) if line.get("at") else datetime.now(),
        status=ReplyStatus(line.get("status") or ReplyStatus.ANSWERED.value),
    )


# @req REQ-HARNESS-009
@backend("git")
@require(HookListen)
@require(HookLoad)
@require(HookForget)
class GitBackend:
    """Appends every message to the run's change's ``chat.jsonl``, holding them until the run has a change.

    Implements REQ-HARNESS-009.
    """

    change: Change | None

    def __init__(self, ws: Workspace, module: Module, change: Change | None) -> None:
        self.ws = ws
        self.module = module
        self.change = change
        #: Lines not written yet: all of them while the run has no change, and any whose write failed.
        self._held: list[dict[str, Any]] = []
        #: The changes there were at start; the first other one found is the run's.
        self._known: set[str] = set() if change is not None else self._active()

    def _active(self) -> set[str]:
        """The names of the module's active changes; none when they cannot be read."""
        try:
            return {c.name for c in list_changes(self.module.config)}
        except Exception:  # noqa: BLE001 - a broken change folder must not stop the chat
            logger.warning("cannot list the changes", exc_info=True)
            return set()

    def _find_change(self) -> None:
        """Make the first change created during the run (the oldest new one) the run's change."""
        try:
            new = [c for c in list_changes(self.module.config) if c.name not in self._known]
        except Exception:  # noqa: BLE001 - a broken change folder must not stop the chat
            logger.warning("cannot list the changes", exc_info=True)
            return
        if new:
            self.change = min(new, key=lambda c: c.order)

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

    async def load(self, since: datetime | None = None, limit: int | None = None) -> list[ChatMessage]:
        """The change's earlier messages, from its ``chat.jsonl``. Implements REQ-HARNESS-009."""
        if self.change is None:
            return []
        try:
            text = (self.change.path / CHAT_FILE).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        found = []
        for raw in text.splitlines():
            try:
                msg = from_line(json.loads(raw))
            except (ValueError, KeyError, TypeError):  # a torn or hand-edited line is skipped
                continue
            if since is None or msg.timestamp >= since:
                found.append(msg)
        return found if limit is None else found[max(len(found) - limit, 0) :]

    async def forget(self, before: datetime | None = None) -> int:
        """Drop held lines (the file is kept); how many were dropped. Implements REQ-HARNESS-009."""
        kept = [] if before is None else [line for line in self._held if datetime.fromisoformat(line["at"]) >= before]
        dropped = len(self._held) - len(kept)
        self._held = kept
        return dropped
