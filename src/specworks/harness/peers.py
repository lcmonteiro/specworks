"""Skill peers: one chatinho ``AgentConnector`` per packaged skill, whose inner agent is a Deep Agent in its workspace."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from chatinho import ChatMessage, Reply, connector
from chatinho.connectors.agent import AgentConnector
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import StructuredTool

from .workspaces import Workspaces

PREFIX = "specworks-"

#: The harness preamble, put before every skill's text; ``{name}`` is the peer, ``{peers}`` every peer joined by ``, ``.
PREAMBLE = (
    "You are the peer `{name}` in a specworks harness chat. The other peers are: {peers}.\n"
    "No one types slash commands here: `/specworks-<name>` in your skill means the peer `<name>`.\n"
    "When your skill stops with a question that only offers the next step, take the option marked (recommended) "
    "and call hand_over with that peer and the change ref; do not ask the user.\n"
    "When your skill asks the user anything else, call ask_user and wait for the answer.\n"
    "When the recommended option is `stop here`, end without calling hand_over."
)


def peer_name(skill: str) -> str:
    """The peer's name: the skill's name without ``specworks-``. Implements REQ-HARNESS-001."""
    raise NotImplementedError


def preamble(name: str, peers: Sequence[str]) -> str:
    """``PREAMBLE`` for the peer ``name`` in a chat of ``peers``. Implements REQ-HARNESS-004."""
    raise NotImplementedError


def skill_instructions(skill: str, peers: Sequence[str]) -> str:
    """The peer's instructions: its preamble, a blank line, then ``read_skill(skill)`` unchanged.

    Implements REQ-HARNESS-001, REQ-HARNESS-004.
    """
    raise NotImplementedError


@connector("skill")
class SkillPeer(AgentConnector):
    """A packaged skill as a chat peer: AgentConnector's graph and chat tools, with a Deep Agent inside.

    It acts only on what is addressed to it, and hands over to the next peer after its run, from a fresh context.
    Implements REQ-HARNESS-002, REQ-HARNESS-003, REQ-HARNESS-005.
    """

    def __init__(self, skill: str, model: BaseChatModel, workspaces: Workspaces, peers: Sequence[str]) -> None:
        """Named ``peer_name(skill)``, with ``ask_user=True`` and ``skill_instructions(skill, peers)`` as its system prompt."""
        raise NotImplementedError

    async def graph(self) -> Any:
        """The compiled graph around a Deep Agent, built per chat shape and workspace. Implements REQ-HARNESS-002."""
        raise NotImplementedError

    async def answer(self, msg: ChatMessage) -> Reply:
        """AgentConnector's run on ``msg``, then the recorded hand-over is said. Implements REQ-HARNESS-003, REQ-HARNESS-005."""
        raise NotImplementedError

    async def listen(self, msg: ChatMessage) -> None:
        """Does nothing: a skill peer acts only on what is addressed to it. Implements REQ-HARNESS-003."""
        raise NotImplementedError

    def hand_over_tool(self) -> StructuredTool:
        """The agent tool ``hand_over(peer: str, text: str) -> str``.

        It returns ``"handed over to <peer>"``, or ``"error: unknown peer '<peer>'"`` / ``"error: cannot hand over to yourself"``
        and records nothing. Implements REQ-HARNESS-003.
        """
        raise NotImplementedError
