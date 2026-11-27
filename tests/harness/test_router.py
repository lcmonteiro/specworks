"""
The harness's router: a message that names no peer goes to the peer a model picks, else to `onboard`, asked of the peers' own model
(REQ-HARNESS-014 to REQ-HARNESS-016).
"""

import asyncio
import logging
from types import SimpleNamespace

import chatinho.support.kits.model.endpoint as endpoint_module
import openai
import pytest
import yaml
from chatinho import LOCAL, ChatSession, HookAnswer, Reply, connector, declares, name_of, require
from chatinho.support.parts.keys.endpoint import Endpoint
from langchain_openai import ChatOpenAI

from harness.scripted import ScriptedModel, User, call, chat, new_change, peer_id, read_chat, settle, touches
from specworks.harness import session as session_module
from specworks.harness.copilot import EDITOR_HEADERS, CopilotSession
from specworks.harness.logins import Login
from specworks.harness.model import MODEL_BASE_URL, MODEL_KEY, MODEL_NAME, model_from_env
from specworks.harness.router import FALLBACK, HarnessRouter, router_endpoint
from specworks.tools.skills import packaged_skills, read_skill
from support.copilot import Clock, FakeGitHub

KEY = "sk-secret"
SETTINGS = {MODEL_KEY: KEY, MODEL_NAME: "gpt-test", MODEL_BASE_URL: "http://127.0.0.1:9/v1"}
OAUTH = "gho_secret"


class FakeOpenAI:
    """
    Stands in for the router's AsyncOpenAI: records each client's key, base URL and headers and each request; answers ``reply``.
    """

    clients: list["FakeOpenAI"] = []
    reply = "everyone"
    error: Exception | None = None
    gate: asyncio.Event | None = None

    def __init__(self, api_key=None, base_url=None, default_headers=None):
        self.api_key = api_key
        self.base_url = base_url
        self.default_headers = dict(default_headers) if default_headers else {}
        self.requests: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        FakeOpenAI.clients.append(self)

    async def _create(self, **params):
        self.requests.append(params)
        if FakeOpenAI.gate is not None:
            await FakeOpenAI.gate.wait()
        if FakeOpenAI.error is not None:
            raise FakeOpenAI.error
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=FakeOpenAI.reply))])

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    async def close(self):
        return None


def routed() -> list[tuple["FakeOpenAI", dict]]:
    """
    Every routing request, with the client that made it, oldest first.
    """
    return [(c, r) for c in FakeOpenAI.clients for r in c.requests]


@pytest.fixture(autouse=True)
def fake_openai(monkeypatch):
    FakeOpenAI.clients = []
    FakeOpenAI.reply = "everyone"
    FakeOpenAI.error = None
    FakeOpenAI.gate = None
    monkeypatch.setattr(endpoint_module, "AsyncOpenAI", FakeOpenAI)
    return FakeOpenAI


@pytest.fixture
def routing(monkeypatch):
    """
    The harness's router asks with a key of its own, so the scripted peers' model needs no network.
    """
    endpoint = Endpoint(api_key="sk-route", model="router-model", base_url="http://router.test/v1")
    monkeypatch.setattr(session_module, "router_endpoint", lambda model: (endpoint, {}))
    return endpoint


def say_to_nobody(text, **kwargs):
    async def then(session, user):
        await user.say(text, **kwargs)

    return then


def answers_to(user, text):
    question = next(m for m in user.messages() if m.text == text)
    return question, user.replies_to(question)


def api_error(message):
    import httpx

    response = httpx.Response(500, request=httpx.Request("POST", "http://router.test/v1/chat/completions"))
    return openai.InternalServerError(message, response=response, body=None)


def front_matter_description(skill):
    text = read_skill(skill)
    return yaml.safe_load(text.split("---", 2)[1])["description"]


# --- REQ-HARNESS-014 -------------------------------------------------------------


# @ac AC-HARNESS-014.1
def test_ac_harness_014_1_the_chosen_peer_answers(project, ws, routing):
    FakeOpenAI.reply = "refine"
    model = ScriptedModel(script={"refine": ["refining"]})
    session, user = chat(ws, model, then=say_to_nobody("let users reset passwords"))
    assert len(routed()) == 1
    question, replies = answers_to(user, "let users reset passwords")
    assert question.to == peer_id(session, "refine")
    assert [m.text for m in replies] == ["refining"]
    assert model.peers_run() == ["refine"]


# @ac AC-HARNESS-014.2
def test_ac_harness_014_2_meant_for_everyone(project, ws, routing):
    FakeOpenAI.reply = "everyone"
    model = ScriptedModel(script={FALLBACK: ["you are at the start"]})
    session, user = chat(ws, model, then=say_to_nobody("hello all"))
    question, replies = answers_to(user, "hello all")
    assert FALLBACK == "onboard"
    assert question.to == peer_id(session, "onboard")
    assert [m.text for m in replies] == ["you are at the start"]
    assert model.peers_run() == ["onboard"]


def unknown_name():
    FakeOpenAI.reply = "nobody"


def failing_request():
    FakeOpenAI.error = api_error("upstream exploded")


def slow_model():
    FakeOpenAI.gate = asyncio.Event()  # never set: the model never answers


# @ac AC-HARNESS-014.3
@pytest.mark.parametrize("script", [unknown_name, failing_request, slow_model], ids=["unknown-name", "api-error", "timeout"])
def test_ac_harness_014_3_a_choice_that_cannot_be_used(project, ws, routing, caplog, script):
    script()
    model = ScriptedModel(script={"onboard": ["here is where you are"]})

    async def then(session, user):
        session.router.timeout = 0.2  # the default is 10 seconds
        await user.say("which way?")

    with caplog.at_level(logging.WARNING):
        session, user = chat(ws, model, then=then)
    question, replies = answers_to(user, "which way?")
    assert question.to == peer_id(session, "onboard")
    assert [m.text for m in replies] == ["here is where you are"]
    assert model.peers_run() == ["onboard"]
    assert any(r.levelno == logging.WARNING and "Routing" in r.getMessage() for r in caplog.records)


# @ac AC-HARNESS-014.4
def test_ac_harness_014_4_addressed_messages_and_replies(project, ws, routing):
    model = ScriptedModel(script={"test": ["tested"], "refine": ["which option?", "option 2 it is"]})

    async def then(session, user):
        await user.say("add a case", to=peer_id(session, "test"))
        await user.say("add x", to=peer_id(session, "refine"))
        await settle()
        asked = next(m for m in user.messages() if m.text == "which option?")
        await user.say("option 2", reply_to=asked.id)

    session, user = chat(ws, model, then=then)
    assert routed() == []
    assert [m.text for m in answers_to(user, "add a case")[1]] == ["tested"]
    reply, answers = answers_to(user, "option 2")
    assert reply.to == peer_id(session, "refine")
    assert [m.text for m in answers] == ["option 2 it is"]


# @ac AC-HARNESS-014.5
def test_ac_harness_014_5_hand_overs(project, ws, routing):
    model = ScriptedModel(script={"refine": [call("hand_over", peer="specify", text="specify add-x"), "refined"], "specify": ["specified"]})
    session, user = chat(ws, model, say="add x")
    assert routed() == []
    assert model.peers_run() == ["refine", "specify"]


# --- REQ-HARNESS-015 -------------------------------------------------------------


@connector("peer")
@require(HookAnswer)
class _Peer:
    def __init__(self, name):
        self.name = name

    async def answer(self, msg):
        return Reply("ok")


def route_once(endpoint, headers):
    """
    One message naming no peer, said in a room of two answering peers routed by a ``HarnessRouter``.
    """

    async def main():
        user = User()
        session = ChatSession(connectors=[_Peer("refine"), _Peer("onboard")], frontend=user, router=HarnessRouter(endpoint, headers=headers))
        await session.start()
        await user.say("hello")
        await asyncio.sleep(0.05)
        await session.close()

    asyncio.run(main())
    assert len(routed()) == 1
    return routed()[0]


# @ac AC-HARNESS-015.1
def test_ac_harness_015_1_the_peers_model_and_key():
    model = model_from_env(SETTINGS)
    client, request = route_once(*router_endpoint(model))
    assert client.base_url == "http://127.0.0.1:9/v1"
    assert client.api_key == KEY
    assert request["model"] == "gpt-test"


def copilot_model(github, clock, root):
    session = CopilotSession(Login(OAUTH), client=github.client(), now=clock.time)
    session.token()
    return ChatOpenAI(model="gpt-test", api_key=session.token, base_url=session.api_base, default_headers=EDITOR_HEADERS), session


# @ac AC-HARNESS-015.2
def test_ac_harness_015_2_a_copilot_login(tmp_path):
    clock = Clock()
    github = FakeGitHub(now=clock.time, valid={OAUTH})
    model, session = copilot_model(github, clock, tmp_path)
    endpoint, headers = router_endpoint(model)
    assert headers == EDITOR_HEADERS
    client, request = route_once(endpoint, headers)
    assert client.base_url == session.api_base
    assert client.api_key == github.last_session(OAUTH)
    assert all(client.default_headers.get(k) == v for k, v in EDITOR_HEADERS.items())
    assert request["model"] == "gpt-test"


# @ac AC-HARNESS-015.3
def test_ac_harness_015_3_a_renewed_token(tmp_path):
    clock = Clock()
    github = FakeGitHub(now=clock.time, valid={OAUTH}, life=25 * 60)
    model, _ = copilot_model(github, clock, tmp_path)
    first = github.last_session(OAUTH)
    endpoint, headers = router_endpoint(model)
    clock.advance(26 * 60)  # the first session token has expired
    client, _ = route_once(endpoint, headers)
    renewed = github.last_session(OAUTH)
    assert renewed != first
    assert client.api_key == renewed
    assert github.device_flows() == 0


# @ac AC-HARNESS-015.4
def test_ac_harness_015_4_the_key_never_shown(project, ws, monkeypatch, caplog):
    endpoint = Endpoint(api_key=KEY, model="router-model", base_url="http://router.test/v1")
    monkeypatch.setattr(session_module, "router_endpoint", lambda model: (endpoint, {}))
    FakeOpenAI.error = api_error(f"Incorrect API key provided: {KEY}")
    change = new_change(project)
    model = ScriptedModel(script={"onboard": [touches(change, "here is where you are")]})  # the run's change is known: chat.jsonl is written

    with caplog.at_level(logging.DEBUG):
        session, user = chat(ws, model, then=say_to_nobody("hello"))
    assert len(routed()) == 1
    assert [m.text for m in answers_to(user, "hello")[1]] == ["here is where you are"]
    assert all(KEY not in m.text for m in user.messages())
    assert KEY not in caplog.text
    assert all(KEY not in r.getMessage() and KEY not in str(r.exc_info or "") for r in caplog.records)
    assert read_chat(change), "the conversation is written"
    assert KEY not in (change.path / "chat.jsonl").read_text(encoding="utf-8")
    assert repr(endpoint).count(KEY) == 0


# --- REQ-HARNESS-016 -------------------------------------------------------------


# @ac AC-HARNESS-016.1
def test_ac_harness_016_1_the_skills_description(project, ws):
    model = ScriptedModel()
    session, user = chat(ws, model)
    peers = {name_of(who): who for at, who in user.peers().items() if at != LOCAL and declares(who, HookAnswer)}
    assert sorted(peers) == sorted(skill.removeprefix("specworks-") for skill in packaged_skills())
    for name, peer in peers.items():
        expected = front_matter_description(f"specworks-{name}")
        assert expected, name
        assert peer.description == expected, name


# @ac AC-HARNESS-016.2
def test_ac_harness_016_2_given_to_the_model(project, ws, routing):
    FakeOpenAI.reply = "refine"
    model = ScriptedModel(script={"refine": ["refining"]})
    chat(ws, model, then=say_to_nobody("let users reset passwords"))
    [(_, request)] = routed()
    prompt = "\n".join(m["content"] for m in request["messages"])
    for skill in packaged_skills():
        name = skill.removeprefix("specworks-")
        assert f"- {name}: {front_matter_description(skill)}" in prompt, name
    assert "let users reset passwords" in prompt


# @ac AC-HARNESS-015.1
def test_ac_harness_015_1_a_key_the_router_cannot_read_falls_back():
    async def key():
        return KEY

    model = ChatOpenAI(model="gpt-test", api_key=key, base_url="http://127.0.0.1:9/v1")
    endpoint, headers = router_endpoint(model)
    assert endpoint.key is None
    assert endpoint.model == "gpt-test"
    assert headers == {}
    assert router_endpoint(ScriptedModel())[0].key is None
