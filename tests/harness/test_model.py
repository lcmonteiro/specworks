"""The harness's model, read from the SPECWORKS_MODEL_* variables, and a key that is never shown (REQ-HARNESS-010)."""

import asyncio
import logging
import sys
from functools import cached_property

import openai
import pytest
from langchain_openai import ChatOpenAI

from harness.scripted import ScriptedModel, chat, new_change, read_chat, touches
from specworks.harness import ModelSettingsError, model_from_env
from specworks.harness.confine import shell_env
from specworks.harness.logins import Login, LoginStore
from specworks.harness.model import MODEL_BASE_URL, MODEL_KEY, MODEL_NAME
from specworks.harness.workspaces import SpecworksWorktrees
from support.copilot import Clock, FakeGitHub

KEY = "sk-secret"
SETTINGS = {MODEL_KEY: KEY, MODEL_NAME: "gpt-test", MODEL_BASE_URL: "http://127.0.0.1:9/v1"}


# @ac AC-HARNESS-010.1
def test_ac_harness_010_1_read_from_the_environment():
    model = model_from_env(dict(SETTINGS))
    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-test"
    assert str(model.openai_api_base) == "http://127.0.0.1:9/v1"
    assert model.openai_api_key is not None and model.openai_api_key.get_secret_value() == KEY


# @ac AC-HARNESS-010.1
def test_ac_harness_010_1_os_environ_by_default(monkeypatch):
    for name, value in SETTINGS.items():
        monkeypatch.setenv(name, value)
    model = model_from_env()
    assert model.model_name == "gpt-test" and model.openai_api_key.get_secret_value() == KEY


# @ac AC-HARNESS-010.2
@pytest.mark.parametrize("variable", [MODEL_KEY, MODEL_NAME])
@pytest.mark.parametrize("value", [None, ""], ids=["missing", "empty"])
def test_ac_harness_010_2_a_missing_variable(variable, value, tmp_path):
    env = dict(SETTINGS)
    if value is None:
        del env[variable]
    else:
        env[variable] = value
    with pytest.raises(ModelSettingsError) as error:
        model_from_env(env, store=LoginStore(tmp_path / "no-logins"))
    assert error.value.variable == variable
    assert variable in str(error.value)
    assert KEY not in str(error.value)
    assert ("specworks login copilot" in str(error.value)) == (variable == MODEL_KEY)


def auth_error():
    """The error an OpenAI-compatible API raises for a bad key, with the key in its message as some APIs echo it."""
    import httpx

    response = httpx.Response(401, request=httpx.Request("POST", "http://127.0.0.1:9/v1/chat/completions"))
    return openai.AuthenticationError(f"Incorrect API key provided: {KEY}", response=response, body=None)


# @ac AC-HARNESS-010.3
def test_ac_harness_010_3_the_key_never_shown(project, ws, monkeypatch, caplog):
    monkeypatch.setenv(MODEL_KEY, KEY)
    change = new_change(project)
    model = ScriptedModel(script={"refine": [touches(change, auth_error())]})
    with caplog.at_level(logging.DEBUG):
        _, user = chat(ws, model, say="add x")
    replies = [m for m in user.messages() if m.frm != 0]
    assert replies, "the failed run must still reply"
    assert all(KEY not in m.text for m in user.messages())
    assert KEY not in caplog.text
    assert all(KEY not in r.getMessage() and KEY not in str(r.exc_info or "") for r in caplog.records)
    assert read_chat(change), "the conversation is written"
    assert KEY not in (change.path / "chat.jsonl").read_text(encoding="utf-8")


# @ac AC-HARNESS-010.3
def test_ac_harness_010_3_the_key_never_in_a_peers_shell(project, ws, monkeypatch):
    for name, value in SETTINGS.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("SPECWORKS_LANGFUSE_SECRET_KEY", "lf-secret")

    async def main():
        checkout = await SpecworksWorktrees(ws).provision("refine", "refine")
        return await checkout.run(f'"{sys.executable}" -c "import os; print(sorted(os.environ.items()))"')

    output = asyncio.run(main())
    assert output.startswith("exit code 0")
    assert "PATH" in output
    assert KEY not in output and "lf-secret" not in output
    assert MODEL_KEY not in output and "SPECWORKS_LANGFUSE_SECRET_KEY" not in output


# @ac AC-HARNESS-010.3
def test_ac_harness_010_3_the_shells_environment():
    env = {"PATH": "/bin", MODEL_KEY: KEY, MODEL_NAME: "gpt-test", "SPECWORKS_LANGFUSE_SECRET_KEY": "lf-secret", "SPECWORKS_OTHER": "kept"}
    assert shell_env(env) == {"PATH": "/bin", "SPECWORKS_OTHER": "kept"}
    assert MODEL_KEY in env, "the given environment is not changed"


OAUTH = "gho_secret"
LOGIN_SETTINGS = {MODEL_NAME: "gpt-test"}


class StoredLogin:
    """A fake GitHub, a store in a temporary folder and a project root, for building a model from a stored login."""

    def __init__(self, tmp_path, **github):
        self.base = tmp_path / "config"
        self.clock = Clock()
        self.github = FakeGitHub(now=self.clock.time, **github)
        self.root = tmp_path / "project"
        self.root.mkdir()

    @cached_property
    def store(self):
        return LoginStore(self.base)

    def stored(self, scope="global", token=OAUTH):
        self.github.valid.add(token)
        self.store.save(scope, self.root if scope == "local" else None, Login(token))

    def model(self, env=None):
        return model_from_env(LOGIN_SETTINGS if env is None else env, root=self.root, store=self.store, client=self.github.client())


@pytest.fixture
def login(tmp_path):
    return StoredLogin(tmp_path)


def key_of(model):
    key = model.openai_api_key
    return key() if callable(key) else key.get_secret_value()


# @ac AC-HARNESS-012.1
def test_ac_harness_012_1_the_key_from_the_login(login):
    login.stored()
    model = login.model()
    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-test"
    assert str(model.openai_api_base).rstrip("/") == "https://api.individual.githubcopilot.com"
    assert key_of(model) == login.github.last_session(OAUTH)
    assert login.github.exchanges() >= 1


# @ac AC-HARNESS-012.1
def test_ac_harness_012_1_the_copilot_api_when_the_exchange_names_none(tmp_path):
    login = StoredLogin(tmp_path, api=None)
    login.stored()
    assert str(login.model().openai_api_base).rstrip("/") == "https://api.githubcopilot.com"


# @ac AC-HARNESS-012.1
def test_ac_harness_012_1_an_empty_key_is_a_missing_one(login):
    login.stored()
    model = login.model({**LOGIN_SETTINGS, MODEL_KEY: "  "})
    assert key_of(model) == login.github.last_session(OAUTH)


# @ac AC-HARNESS-012.2
def test_ac_harness_012_2_local_before_global(login):
    login.stored("global", "gho_secret_global")
    login.stored("local", "gho_secret_local")
    model = login.model()
    assert key_of(model) == login.github.last_session("gho_secret_local")
    assert "gho_secret_global" not in login.github.sessions, "the global login is not exchanged"


# @ac AC-HARNESS-012.3
def test_ac_harness_012_3_an_explicit_key_wins(login, monkeypatch):
    login.stored()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("a stored login was read")

    monkeypatch.setattr(LoginStore, "find", forbidden)
    monkeypatch.setattr(LoginStore, "load", forbidden)
    model = login.model(dict(SETTINGS))
    assert key_of(model) == KEY
    assert login.github.requests == [], "no exchange is made"


# @ac AC-HARNESS-012.6
def test_ac_harness_012_6_the_base_url_set_by_the_user(login):
    login.stored()
    model = login.model({**LOGIN_SETTINGS, MODEL_BASE_URL: "http://127.0.0.1:9/v1"})
    assert str(model.openai_api_base) == "http://127.0.0.1:9/v1"
    assert key_of(model) == login.github.last_session(OAUTH)


# @ac AC-HARNESS-010.4
def test_ac_harness_010_4_a_logins_tokens_never_shown(project, ws, login, caplog):
    login.stored()
    model = login.model()
    session_token = login.github.last_session(OAUTH)
    assert OAUTH not in repr(model) and session_token not in repr(model)

    def echoing_error():
        """An API error that repeats both tokens, as some APIs echo the credentials they got."""
        import httpx

        response = httpx.Response(401, request=httpx.Request("POST", "http://127.0.0.1:9/v1/chat/completions"))
        return openai.AuthenticationError(f"Incorrect credentials: {OAUTH} {session_token}", response=response, body=None)

    change = new_change(project)
    scripted = ScriptedModel(script={"refine": [touches(change, echoing_error())]})
    with caplog.at_level(logging.DEBUG):
        _, user = chat(ws, scripted, say="add x")
    replies = [m for m in user.messages() if m.frm != 0]
    assert replies, "the failed run must still reply"
    for token in (OAUTH, session_token):
        assert all(token not in m.text for m in user.messages())
        assert token not in caplog.text
        assert read_chat(change), "the conversation is written"
        assert token not in (change.path / "chat.jsonl").read_text(encoding="utf-8")
