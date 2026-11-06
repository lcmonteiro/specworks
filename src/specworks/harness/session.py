"""The harness session: the user, one skill peer per packaged skill, the git backend and the workspace commands."""

from __future__ import annotations

from typing import Any

from chatinho import ChatSession
from langchain_core.language_models import BaseChatModel

from ..core.changes import Change
from ..core.workspace import Workspace


def first_peer(change: Change | None) -> str:
    """The peer the user's first message goes to: ``refine`` without a change, else the peer of its phase. Implements REQ-CLI-022."""
    raise NotImplementedError


def build_harness(ws: Workspace, model: BaseChatModel, *, request: str | None = None, change: Change | None = None, frontend: Any = None) -> ChatSession:
    """The harness session; ``frontend=None`` builds the terminal.

    The request is said by the user to ``first_peer(change)`` once the session starts. Implements REQ-HARNESS-001, REQ-CLI-022.
    """
    raise NotImplementedError


def run_harness(ws: Workspace, request: str | None, change: Change | None) -> None:
    """Read the model (``model_from_env()``, before anything opens), then build and run the harness. Implements REQ-CLI-022."""
    raise NotImplementedError
