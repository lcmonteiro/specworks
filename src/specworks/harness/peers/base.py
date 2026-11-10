"""The skill peers' base: ``SkillPeer``, a chatinho ``DeepAgentConnector`` per packaged skill, and the preamble every peer gets."""

from __future__ import annotations

import asyncio
import contextvars
import logging
from collections.abc import Sequence
from typing import ClassVar

from chatinho import ChatMessage, Query, Reply, ReplyStatus, name_of
from chatinho.connectors.deep import DeepAgentConnector
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import StructuredTool

from ...tools.skills import read_skill

logger = logging.getLogger(__name__)

PREFIX = "specworks-"

#: The harness preamble, put before every skill's text; ``{name}`` is the peer, ``{peers}`` every peer joined by ``, ``.
PREAMBLE = (
    "You are the peer `{name}` in a specworks harness chat. The other peers are: {peers}.\n"
    "No one types slash commands here: `/specworks-<name>` in your skill means the peer `<name>`.\n"
    "When your skill stops with a question that only offers the next step, take the option marked (recommended) "
    "and call hand_over with that peer and the change ref; do not ask the user.\n"
    "When your skill asks the user anything else, call ask_user and wait for the answer.\n"
    "When the recommended option is `stop here`, end without calling hand_over.\n"
    "When your skill merges a worktree's branch, do not merge it yourself: call ask_user asking the user to run `/merge <name>`, and wait."
)

#: The preamble rule for the peer whose skill merges a worktree's branch (``build``), added after ``PREAMBLE``.
MERGE_RULE = "When your skill merges a worktree's branch, do not merge it yourself: call ask_user asking the user to run `/merge <name>`, and wait."


#: What a skill peer remembers: the conversation as the backend keeps it, every peer's messages, the newest ones.
MEMORY = Query().last(100)

#: The hand-overs the run in progress recorded, as (peer id, text); one list per run of ``answer``.
_HANDED: contextvars.ContextVar[list[tuple[int, str]] | None] = contextvars.ContextVar("specworks_handed", default=None)


# @req REQ-HARNESS-001
def peer_name(skill: str) -> str:
    """The peer's name: the skill's name without ``specworks-``. Implements REQ-HARNESS-001."""
    return skill.removeprefix(PREFIX)


# @req REQ-HARNESS-004
def preamble(name: str, peers: Sequence[str], rules: Sequence[str] = ()) -> str:
    """``PREAMBLE`` for the peer ``name`` in a chat of ``peers``, then each of ``rules`` on its own line. Implements REQ-HARNESS-004."""
    if rules:
        raise NotImplementedError("preamble rules")
    return PREAMBLE.format(name=name, peers=", ".join(peers))


# @req REQ-HARNESS-001
# @req REQ-HARNESS-004
def skill_instructions(skill: str, peers: Sequence[str], rules: Sequence[str] = ()) -> str:
    """The peer's instructions: its preamble (with ``rules``), a blank line, then ``read_skill(skill)`` unchanged.

    Implements REQ-HARNESS-001, REQ-HARNESS-004.
    """
    return preamble(peer_name(skill), peers, rules) + "\n\n" + read_skill(skill)


# @req REQ-HARNESS-002
# @req REQ-HARNESS-003
# @req REQ-HARNESS-005
class SkillPeer(DeepAgentConnector):
    """A packaged skill as a chat peer: chatinho's Deep Agent connector, in the workspace the provider gives it.

    Each step is a subclass in its own module, named by ``@connector("<name>")``; its skill is ``PREFIX + name``.
    It acts only on what is addressed to it, and hands over to the next peer after its run, from a fresh context.
    Implements REQ-HARNESS-001, REQ-HARNESS-002, REQ-HARNESS-003, REQ-HARNESS-005.
    """

    #: The peer's name, set on each subclass by ``@connector("<name>")``. Implements REQ-HARNESS-001.
    name: str = "skill"
    #: The step works in a git worktree of its own instead of the main checkout. Implements REQ-HARNESS-006.
    worktree: ClassVar[bool] = False
    #: Preamble lines this step gets after the common ones. Implements REQ-HARNESS-004.
    rules: ClassVar[tuple[str, ...]] = ()

    @classmethod
    def skill_name(cls) -> str:
        """The packaged skill this class serves: ``PREFIX + cls.name``. Implements REQ-HARNESS-001."""
        return PREFIX + cls.name

    def __init__(self, model: BaseChatModel, peers: Sequence[str]) -> None:
        """Named ``cls.name``: ``ask_user=True``, ``MEMORY``, the ``hand_over`` tool and ``skill_instructions(skill, peers, rules)``.

        Implements REQ-HARNESS-001, REQ-HARNESS-002.
        """
        skill = self.skill_name()
        self.skill = skill
        #: The skill peers' names, which ``hand_over`` accepts (all but its own).
        self.peer_names = list(peers)
        #: Hand-overs being said; kept so they are not collected before they run.
        self._handing: set[asyncio.Task[None]] = set()
        super().__init__(peer_name(skill), model, [self.hand_over_tool()], memory=MEMORY, ask_user=True, system_prompt=skill_instructions(skill, peers, self.rules))

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
