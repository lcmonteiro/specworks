"""The harness's chat model, read from the ``SPECWORKS_MODEL_*`` variables; a key's value is never shown."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

import httpx
from langchain_core.language_models import BaseChatModel

from specworks.core.errors import SpecworksError
from specworks.harness.copilot import EDITOR_HEADERS, CopilotSession
from specworks.harness.logins import LoginStore

MODEL_KEY = "SPECWORKS_MODEL_API_KEY"
MODEL_NAME = "SPECWORKS_MODEL_MODEL"
MODEL_BASE_URL = "SPECWORKS_MODEL_BASE_URL"


# @req REQ-HARNESS-010
class ModelSettingsError(SpecworksError):
    """A model setting is missing or empty; the message names the variable, never a value. Implements REQ-HARNESS-010."""

    def __init__(self, variable: str) -> None:
        hint = " (or run `specworks login copilot`)" if variable == MODEL_KEY else ""
        super().__init__(f"{variable} is not set{hint}")
        self.variable = variable


# @req REQ-HARNESS-010
# @req REQ-HARNESS-012
def model_from_env(
    env: Mapping[str, str] | None = None,
    *,
    root: Path | None = None,
    store: LoginStore | None = None,
    client: httpx.Client | None = None,
) -> BaseChatModel:
    """An OpenAI-compatible chat model from ``env`` (``os.environ`` when None).

    Raises ``ModelSettingsError`` for the first of ``MODEL_KEY``, ``MODEL_NAME`` missing or empty. When the key is missing or empty, the stored
    Copilot login of ``root`` (``store``, ``client``) is used instead, and the error says to run ``specworks login copilot``.
    Implements REQ-HARNESS-010, REQ-HARNESS-012.
    """
    env = os.environ if env is None else env
    explicit_key = bool(env.get(MODEL_KEY, "").strip())
    # An explicit key wins: the stored logins are then neither read nor used.
    login = None if explicit_key else (LoginStore() if store is None else store).find(root)
    if not explicit_key and login is None:
        raise ModelSettingsError(MODEL_KEY)
    if not env.get(MODEL_NAME, "").strip():
        raise ModelSettingsError(MODEL_NAME)
    from langchain_openai import ChatOpenAI  # here, so building the model is the only place that needs it
    from pydantic import SecretStr

    base_url = env.get(MODEL_BASE_URL) or None
    if login is None:
        # The key is a SecretStr, so the model's repr and its errors never show it.
        return ChatOpenAI(model=env[MODEL_NAME], api_key=SecretStr(env[MODEL_KEY]), base_url=base_url)
    session = CopilotSession(login, client=client)
    session.token()  # the first exchange gives the API base, and fails now, not mid-chat, for a login GitHub no longer accepts
    return ChatOpenAI(model=env[MODEL_NAME], api_key=session.token, base_url=base_url or session.api_base, default_headers=EDITOR_HEADERS)
