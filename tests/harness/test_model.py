"""The harness's model, read from the SPECWORKS_MODEL_* variables, and a key that is never shown (REQ-HARNESS-010)."""

import asyncio
import logging
import sys

import openai
import pytest
from langchain_openai import ChatOpenAI

from harness.scripted import ScriptedModel, chat, new_change, read_chat
from specworks.harness import ModelSettingsError, model_from_env
from specworks.harness.confine import shell_env
from specworks.harness.model import MODEL_BASE_URL, MODEL_KEY, MODEL_NAME
from specworks.harness.workspaces import SpecworksWorktrees

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
def test_ac_harness_010_2_a_missing_variable(variable, value):
    env = dict(SETTINGS)
    if value is None:
        del env[variable]
    else:
        env[variable] = value
    with pytest.raises(ModelSettingsError) as error:
        model_from_env(env)
    assert error.value.variable == variable
    assert variable in str(error.value)
    assert KEY not in str(error.value)


def auth_error():
    """The error an OpenAI-compatible API raises for a bad key, with the key in its message as some APIs echo it."""
    import httpx

    response = httpx.Response(401, request=httpx.Request("POST", "http://127.0.0.1:9/v1/chat/completions"))
    return openai.AuthenticationError(f"Incorrect API key provided: {KEY}", response=response, body=None)


# @ac AC-HARNESS-010.3
def test_ac_harness_010_3_the_key_never_shown(project, ws, monkeypatch, caplog):
    monkeypatch.setenv(MODEL_KEY, KEY)
    change = new_change(project)
    model = ScriptedModel(script={"refine": [auth_error()]})
    with caplog.at_level(logging.DEBUG):
        _, user = chat(ws, model, request="add x", change=change)
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
