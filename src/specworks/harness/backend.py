"""The git backend: the conversation kept in a git-ignored ``chat.jsonl`` in the run's change folder."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from chatinho import ChatMessage, HookForget, HookListen, HookLoad, backend, require

from ..core.changes import Change
from ..core.workspace import Module, Workspace

CHAT_FILE = "chat.jsonl"


def to_line(msg: ChatMessage) -> dict[str, Any]:
    """``msg`` as a ``chat.jsonl`` line: ``id``, ``from``, ``to``, ``replyTo``, ``status``, ``text``, ``at``; never its credentials.

    Implements REQ-HARNESS-009.
    """
    raise NotImplementedError


def from_line(line: dict[str, Any]) -> ChatMessage:
    """The message a ``chat.jsonl`` line holds. Implements REQ-HARNESS-009."""
    raise NotImplementedError


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
        raise NotImplementedError

    async def listen(self, msg: ChatMessage) -> None:
        """Append ``msg`` (or hold it while the run has no change); a write failure is logged and ignored. Implements REQ-HARNESS-009."""
        raise NotImplementedError

    async def load(self, since: datetime | None = None, limit: int | None = None) -> list[ChatMessage]:
        """The change's earlier messages, from its ``chat.jsonl``. Implements REQ-HARNESS-009."""
        raise NotImplementedError

    async def forget(self, before: datetime | None = None) -> int:
        """Drop held lines (the file is kept); how many were dropped. Implements REQ-HARNESS-009."""
        raise NotImplementedError
