"""The harness tests' scripted chat: a chat model with no network, a user who answers from a list, and a driver.

The harness gives one model to every skill peer, so the script is keyed by peer: the model reads which peer is
running from the preamble in its system prompt (``You are the peer `<name>` ...``). Each step is one model call:
- a string: the model answers that text;
- a ``call(name, **args)``: the model calls that tool (the agent then runs it and calls the model again);
- an exception: the model raises it;
- a function of the messages: what it returns is the step.
When a peer's steps run out, it answers ``done``. Every call is recorded in ``calls``.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import threading
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from chatinho import ChatMessage, HookAnswer, HookContext, HookListen, HookPeers, HookSay, Reply, frontend, require
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import ConfigDict, Field, PrivateAttr

from helpers import git, init_repo, runner
from specworks.cli import app
from specworks.core.changes import Change, load_change, set_phase
from specworks.core.workspace import load_workspace
from specworks.harness import build_harness

BRANCH = "add-x"
CHANGE = "add-x"
PEER_RE = re.compile(r"You are the peer `([^`]+)`")
DEFAULT = "done"
#: How long a scripted chat may take to go quiet, in seconds.
SETTLE_TIMEOUT = 30.0


@dataclass(frozen=True)
class call:  # noqa: N801 - reads as a step in a script: call("hand_over", peer="specify", text="...")
    """A step that calls the tool ``name`` with ``args``."""

    name: str
    args: dict[str, Any] = field(default_factory=dict)

    def __init__(self, name: str, **args: Any) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "args", args)


@dataclass
class Call:
    """One model call: the peer running, the messages it was given, and the names of the tools it was given."""

    peer: str | None
    messages: list[BaseMessage]
    tools: list[str]

    @property
    def system(self) -> str:
        """The system prompt's text."""
        return "\n".join(m.text for m in self.messages if isinstance(m, SystemMessage))

    @property
    def human(self) -> list[str]:
        """The text of every human message (memory and the question), in order."""
        return [m.text for m in self.messages if isinstance(m, HumanMessage)]

    def tool_results(self) -> list[str]:
        """The text of every tool result in the messages, in order."""
        return [m.text for m in self.messages if isinstance(m, ToolMessage)]


def peer_of(messages: Sequence[BaseMessage]) -> str | None:
    """The peer named by the preamble in the system prompt, or None."""
    for m in messages:
        if isinstance(m, SystemMessage):
            found = PEER_RE.search(m.text)
            if found:
                return found.group(1)
    return None


class ScriptedModel(BaseChatModel):
    """A chat model that answers from ``script`` ({peer: [step, ...]}); see the module's docstring."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    script: dict[str, list[Any]] = Field(default_factory=dict)
    calls: list[Call] = Field(default_factory=list)
    _lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)
    _ids: int = PrivateAttr(default=0)

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: Sequence[Any], *, tool_choice: str | None = None, **kwargs: Any) -> Runnable[Any, AIMessage]:
        names = [convert_to_openai_tool(t)["function"]["name"] for t in tools]
        return self.bind(tool_names=names, **kwargs)

    def runs_of(self, peer: str) -> list[Call]:
        """The calls made while ``peer`` was running."""
        return [c for c in self.calls if c.peer == peer]

    def peers_run(self) -> list[str]:
        """The peers that called the model, in the order of their first call."""
        seen: list[str] = []
        for c in self.calls:
            if c.peer is not None and c.peer not in seen:
                seen.append(c.peer)
        return seen

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        tool_names: list[str] | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        peer = peer_of(messages)
        with self._lock:
            self.calls.append(Call(peer, list(messages), list(tool_names or [])))
            steps = self.script.get(peer or "", [])
            step: Any = steps.pop(0) if steps else DEFAULT
            self._ids += 1
            n = self._ids
        while callable(step) and not isinstance(step, BaseException):
            step = step(messages)
        if isinstance(step, BaseException):
            raise step
        if isinstance(step, call):
            message = AIMessage(content="", tool_calls=[{"name": step.name, "args": step.args, "id": f"call-{n}", "type": "tool_call"}])
        else:
            message = AIMessage(content=str(step))
        return ChatResult(generations=[ChatGeneration(message=message)])


@frontend("me")
@require(HookSay)
@require(HookListen)
@require(HookAnswer)
@require(HookContext)
@require(HookPeers)
class User:
    """The user, without a terminal: hears everything, and answers each question put to it with the next of ``answers``."""

    def __init__(self, answers: Sequence[str] = ()) -> None:
        self.answers = list(answers)
        self.heard: list[ChatMessage] = []
        self.asked: list[ChatMessage] = []

    async def listen(self, msg: ChatMessage) -> None:
        self.heard.append(msg)

    async def answer(self, msg: ChatMessage) -> Reply:
        self.asked.append(msg)
        return Reply(self.answers.pop(0) if self.answers else "ok")

    def messages(self) -> list[ChatMessage]:
        """The whole conversation, oldest first."""
        return self.context()  # type: ignore[attr-defined]  # granted by HookContext

    def replies_to(self, msg: ChatMessage) -> list[ChatMessage]:
        return [m for m in self.messages() if m.reply_to == msg.id]


async def settle(timeout: float = SETTLE_TIMEOUT) -> None:
    """Wait until every other task of the loop is done: the chat has gone quiet."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    current = asyncio.current_task()
    quiet = 0
    while quiet < 3:  # quiet for a few turns of the loop in a row, so a task scheduled by one just finishing is seen
        busy = [t for t in asyncio.all_tasks() if t is not current and not t.done()]
        quiet = 0 if busy else quiet + 1
        if loop.time() > deadline:
            raise AssertionError(f"the chat did not go quiet in {timeout}s: {busy}")
        await asyncio.sleep(0.02)


Then = Callable[[Any, User], Awaitable[None]]


def chat(ws: Any, model: BaseChatModel, *, request: str | None = None, change: Any = None, user: User | None = None, then: Then | None = None, max_depth: int | None = None) -> tuple[Any, User]:
    """Build the harness with ``user`` as its frontend, start it, run ``then(session, user)``, wait until quiet, close it."""
    user = user or User()

    async def main() -> Any:
        session = build_harness(ws, model, request=request, change=change, frontend=user)
        if max_depth is not None:
            session.max_depth = max_depth
        await session.start()
        await settle()
        if then is not None:
            await then(session, user)
            await settle()
        await session.close()
        return session

    return asyncio.run(main()), user


def peer_id(session: Any, name: str) -> int:
    at = session.id_of(name)
    assert at is not None, f"no peer {name}"
    return at


# --- a project in a git repository ---------------------------------------------


def make_project(root: Path, monkeypatch: Any) -> Path:
    """A specworks project committed on `main`, checked out on the branch `add-x`, with no change yet."""
    monkeypatch.chdir(root)
    for key, value in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(key, value)
    init_repo(root)
    result = runner.invoke(app, ["init", "--no-skills"])
    assert result.exit_code == 0, result.output
    commit_all(root, "baseline")
    git(root, "checkout", "-q", "-b", BRANCH)
    return root


def commit_all(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-q", "--allow-empty", "-m", message)


def git_out(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


def head(root: Path) -> str:
    return git_out(root, "rev-parse", "HEAD").strip()


def new_change(root: Path, phase: str = "refine", name: str = CHANGE) -> Change:
    """The change `name` in `phase`, committed."""
    result = runner.invoke(app, ["new", name, "--no-branch"])
    assert result.exit_code == 0, result.output
    config = load_workspace(root).top.config
    if phase != "refine":
        set_phase(load_change(config, name), phase)
    commit_all(root, f"{name}: {phase}")
    return load_change(config, name)


def write_chat(change: Change, lines: Sequence[dict[str, Any]]) -> None:
    """An earlier conversation in the change's ``chat.jsonl``, one JSON line per message."""
    text = "".join(json.dumps(line) + "\n" for line in lines)
    (change.path / "chat.jsonl").write_text(text, encoding="utf-8")


def read_chat(change: Change) -> list[dict[str, Any]]:
    path = change.path / "chat.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
