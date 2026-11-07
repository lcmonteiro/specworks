"""The harness session: the user, one skill peer per packaged skill, the git backend, the workspaces and their commands."""

from __future__ import annotations

from typing import Any

from chatinho import LOCAL, ChatSession, WorkspaceCommand
from chatinho.routers import SimpleRouter
from langchain_core.language_models import BaseChatModel

from ..core.changes import Change
from ..core.workspace import Workspace
from ..tools.skills import packaged_skills
from .backend import GitBackend
from .model import model_from_env
from .peers import SkillPeer, peer_name
from .workspaces import MergeCommand, SpecworksWorktrees

#: The peer that carries on a change in each phase; a baseline change goes to `baseline` from specify to review.
PHASE_PEERS = {
    "refine": "refine",
    "specify": "specify",
    "design": "build",
    "implement": "build",
    "review": "build",
    "validate": "done",
    "close": "done",
    "done": "done",
}
BASELINE_PHASES = ("specify", "design", "implement", "review")


# @req REQ-CLI-022
def first_peer(change: Change | None) -> str:
    """The peer the user's first message goes to: ``refine`` without a change, else the peer of its phase. Implements REQ-CLI-022."""
    if change is None:
        return "refine"
    if change.name.startswith("baseline-") and change.phase in BASELINE_PHASES:
        return "baseline"
    return PHASE_PEERS.get(change.phase, "refine")


class HarnessSession(ChatSession):
    """A chat session that says the user's request to its first peer once it has started (and loaded the conversation)."""

    def __init__(self, *args: Any, request: str | None = None, first: str = "refine", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.request = request
        self.first = first

    async def start(self) -> None:
        await super().start()
        request, self.request = self.request, None  # said once, however often start() runs
        at = self.id_of(self.first)
        if request and at is not None:
            await self._say_for(LOCAL)(request, to=at)


# @req REQ-HARNESS-001
# @req REQ-CLI-022
def build_harness(ws: Workspace, model: BaseChatModel, *, request: str | None = None, change: Change | None = None, frontend: Any = None) -> ChatSession:
    """The harness session; ``frontend=None`` builds the terminal.

    The request is said by the user to ``first_peer(change)`` once the session starts. Implements REQ-HARNESS-001, REQ-CLI-022.
    """
    module = ws.owner(change.path) if change is not None else ws.current
    skills = packaged_skills()
    names = [peer_name(skill) for skill in skills]
    provider = SpecworksWorktrees(ws)
    backend = GitBackend(ws, module, change)
    if frontend is None:
        from chatinho.frontends.chat import ChatFrontend  # the terminal: only when one is opened

        frontend = ChatFrontend(title="specworks harness", name="me", welcome_message=f"Peers: {', '.join(names)}. Ask one with @<peer> <text>.")
    return HarnessSession(
        connectors=[SkillPeer(skill, model, names) for skill in skills],
        commands=[WorkspaceCommand(provider), MergeCommand(provider, backend)],
        workspaces=provider,
        frontend=frontend,
        backend=backend,
        router=SimpleRouter(),
        request=request,
        first=first_peer(change),
    )


# @req REQ-CLI-022
def run_harness(ws: Workspace, request: str | None, change: Change | None) -> None:
    """Read the model (``model_from_env()``, before anything opens), then build and run the harness. Implements REQ-CLI-022."""
    model = model_from_env()
    build_harness(ws, model, request=request, change=change).run()
