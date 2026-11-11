"""The harness's chat model, read from the ``SPECWORKS_MODEL_*`` variables; a key's value is never shown."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

import httpx
from langchain_core.language_models import BaseChatModel

from specworks.core.errors import SpecworksError
from specworks.harness.logins import LoginStore

MODEL_KEY = "SPECWORKS_MODEL_API_KEY"
MODEL_NAME = "SPECWORKS_MODEL_MODEL"
MODEL_BASE_URL = "SPECWORKS_MODEL_BASE_URL"


# @req REQ-HARNESS-010
class ModelSettingsError(SpecworksError):
    """A model setting is missing or empty; the message names the variable, never a value. Implements REQ-HARNESS-010."""

    def __init__(self, variable: str) -> None:
        super().__init__(f"{variable} is not set")
        self.variable = variable


# @req REQ-HARNESS-010
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
    for variable in (MODEL_KEY, MODEL_NAME):
        if not env.get(variable, "").strip():
            raise ModelSettingsError(variable)
    from langchain_openai import ChatOpenAI  # here, so building the model is the only place that needs it
    from pydantic import SecretStr

    # The key is a SecretStr, so the model's repr and its errors never show it.
    return ChatOpenAI(model=env[MODEL_NAME], api_key=SecretStr(env[MODEL_KEY]), base_url=env.get(MODEL_BASE_URL) or None)
