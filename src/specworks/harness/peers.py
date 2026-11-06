"""Skill peers: one chatinho ``AgentConnector`` per packaged skill, whose inner agent is a Deep Agent in its workspace."""

from __future__ import annotations

import asyncio
import contextvars
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from chatinho import ChatMessage, Query, Reply, ReplyStatus, connector, name_of
from chatinho.connectors.agent import AgentConnector
from deepagents import create_deep_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import StructuredTool

from ..tools.skills import read_skill
from .confine import PeerShell
from .workspaces import Workspaces

logger = logging.getLogger(__name__)

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


#: What a skill peer remembers: the conversation as the backend keeps it, every peer's messages, the newest ones.
MEMORY = Query().last(100)

#: The hand-overs the run in progress recorded, as (peer id, text); one list per run of ``answer``.
_HANDED: contextvars.ContextVar[list[tuple[int, str]] | None] = contextvars.ContextVar("specworks_handed", default=None)


# @req REQ-HARNESS-001
def peer_name(skill: str) -> str:
    """The peer's name: the skill's name without ``specworks-``. Implements REQ-HARNESS-001."""
    return skill.removeprefix(PREFIX)


# @req REQ-HARNESS-004
def preamble(name: str, peers: Sequence[str]) -> str:
    """``PREAMBLE`` for the peer ``name`` in a chat of ``peers``. Implements REQ-HARNESS-004."""
    return PREAMBLE.format(name=name, peers=", ".join(peers))


# @req REQ-HARNESS-001
# @req REQ-HARNESS-004
def skill_instructions(skill: str, peers: Sequence[str]) -> str:
    """The peer's instructions: its preamble, a blank line, then ``read_skill(skill)`` unchanged.

    Implements REQ-HARNESS-001, REQ-HARNESS-004.
    """
    return preamble(peer_name(skill), peers) + "\n\n" + read_skill(skill)


# @req REQ-HARNESS-002
# @req REQ-HARNESS-003
# @req REQ-HARNESS-005
@connector("skill")
class SkillPeer(AgentConnector):
    """A packaged skill as a chat peer: AgentConnector's graph and chat tools, with a Deep Agent inside.

    It acts only on what is addressed to it, and hands over to the next peer after its run, from a fresh context.
    Implements REQ-HARNESS-002, REQ-HARNESS-003, REQ-HARNESS-005.
    """

    def __init__(self, skill: str, model: BaseChatModel, workspaces: Workspaces, peers: Sequence[str]) -> None:
        """Named ``peer_name(skill)``, with ``ask_user=True`` and ``skill_instructions(skill, peers)`` as its system prompt."""
        self.skill = skill
        self.workspaces = workspaces
        #: The skill peers' names, which ``hand_over`` accepts (all but its own).
        self.peer_names = list(peers)
        super().__init__(peer_name(skill), model, [self.hand_over_tool()], memory=MEMORY, ask_user=True, system_prompt=skill_instructions(skill, peers))
        #: The one backend of this peer's Deep Agent, following its workspace on every call.
        self.shell = PeerShell(self._workspace)
        #: The compiled graphs, by chat shape (the shell follows the workspace by itself).
        self._graphs: dict[Any, Any] = {}
        #: Hand-overs being said; kept so they are not collected before they run.
        self._handing: set[asyncio.Task[None]] = set()

    def _workspace(self) -> Path:
        """The folder of this peer's workspace (the main checkout until it opens another)."""
        me = getattr(self, "peer_id", None)
        return self.workspaces.ws.root if me is None else self.workspaces.path_of(me)

    async def graph(self) -> Any:
        """The compiled graph around a Deep Agent over ``shell``, built per chat shape. Implements REQ-HARNESS-002, REQ-HARNESS-006."""
        shape = self._shape()
        async with self._building:
            built = self._graphs.get(shape)
            if built is None:
                # AgentConnector.graph(), with a Deep Agent over the peer's shell in place of create_agent.
                tools = self.tools + self._chat_tools(shape)
                options = {k: v for k, v in self.options.items() if k != "checkpointer"}
                inner = create_deep_agent(self.model, tools, backend=self.shell, **options)
                built = self._graphs[shape] = self._compile(inner)
            return built

    async def answer(self, msg: ChatMessage) -> Reply:
        """AgentConnector's run on ``msg``, then the recorded hand-over is said. Implements REQ-HARNESS-003, REQ-HARNESS-005."""
        handed: list[tuple[int, str]] = []
        token = _HANDED.set(handed)
        try:
            reply = await super().answer(msg)
        finally:
            _HANDED.reset(token)
        if reply.status is not ReplyStatus.ERROR:
            for at, text in handed:
                # From an empty context, so the next stage is asked at depth one instead of one deeper than this one.
                task = asyncio.create_task(self._hand_over(at, text, msg), context=contextvars.Context())
                self._handing.add(task)
                task.add_done_callback(self._handing.discard)
        return reply

    async def _hand_over(self, at: int, text: str, msg: ChatMessage) -> None:
        """Say ``text`` to peer ``at``, replying to ``msg``, once this peer's reply to it is posted."""
        await asyncio.sleep(0)  # the session posts the reply as soon as answer() returns
        try:
            await self.say(text, to=at, reply_to=msg.id)
        except Exception as exc:  # noqa: BLE001 - a peer that left the chat must not take this one down
            logger.warning("%s: cannot hand over (%s)", self.name, type(exc).__name__)

    async def listen(self, msg: ChatMessage) -> None:
        """Does nothing: a skill peer acts only on what is addressed to it. Implements REQ-HARNESS-003."""
        return None

    def hand_over_tool(self) -> StructuredTool:
        """The agent tool ``hand_over(peer: str, text: str) -> str``.

        It returns ``"handed over to <peer>"``, or ``"error: unknown peer '<peer>'"`` / ``"error: cannot hand over to yourself"``
        and records nothing. Implements REQ-HARNESS-003.
        """

        async def hand_over(peer: str, text: str) -> str:
            if peer == self.name:
                return "error: cannot hand over to yourself"
            at = next((at for at, who in self.peers().items() if name_of(who) == peer), None) if peer in self.peer_names else None
            if at is None:
                return f"error: unknown peer '{peer}'"
            handed = _HANDED.get()
            if handed is None:  # only a run of answer() records hand-overs
                return "error: hand_over works only while answering a message"
            handed.append((at, text))
            return f"handed over to {peer}"

        return StructuredTool.from_function(
            coroutine=hand_over,
            name="hand_over",
            description=(
                "Hand the work over to another peer of this chat (a skill, e.g. specify) with a message for it, such as the "
                "change ref and what to do. It is said once your answer is posted; it does not wait for that peer."
            ),
        )
