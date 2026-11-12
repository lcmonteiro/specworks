"""
The harness session: the user, one skill peer per packaged skill, the git backend, the workspaces and their commands.
"""

from __future__ import annotations

from typing import Any

from chatinho import ChatSession, WorkspaceCommand
from chatinho.routers import SimpleRouter
from langchain_core.language_models import BaseChatModel

from specworks.core.workspace import Workspace
from specworks.harness.backend import GitBackend
from specworks.harness.model import model_from_env
from specworks.harness.peers import PEERS, worktree_peers
from specworks.harness.workspaces import MergeCommand, SpecworksWorktrees


# @req REQ-HARNESS-001
# @req REQ-HARNESS-006
# @req REQ-CLI-022
def build_harness(ws: Workspace, model: BaseChatModel, *, frontend: Any = None) -> ChatSession:
    """
    The harness session, with an empty conversation and nothing said for the user; ``frontend=None`` builds the terminal.

    Implements REQ-HARNESS-001, REQ-HARNESS-006, REQ-CLI-022.
    """
    module = ws.current
    names = [cls.name for cls in PEERS]
    provider = SpecworksWorktrees(ws, worktree_peers(PEERS))
    backend = GitBackend(ws, module)
    if frontend is None:
        from chatinho.frontends.chat import ChatFrontend  # the terminal: only when one is opened

        frontend = ChatFrontend(title="specworks harness", name="me", welcome_message=f"Peers: {', '.join(names)}. Ask one with @<peer> <text>.")
    return ChatSession(
        connectors=[cls(model, names) for cls in PEERS],
        commands=[WorkspaceCommand(provider), MergeCommand(provider, backend)],
        workspaces=provider,
        frontend=frontend,
        backend=backend,
        router=SimpleRouter(),
    )


# @req REQ-CLI-022
def run_harness(ws: Workspace) -> None:
    """
    Read the model (``model_from_env()``, before anything opens), then build and run the harness. Implements REQ-CLI-022.
    """
    model = model_from_env(root=ws.root)
    build_harness(ws, model).run()
