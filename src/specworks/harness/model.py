"""The harness's chat model, read from the ``SPECWORKS_MODEL_*`` variables; a key's value is never shown."""

from __future__ import annotations

from collections.abc import Mapping

from langchain_core.language_models import BaseChatModel

from ..core.errors import SpecworksError

MODEL_KEY = "SPECWORKS_MODEL_API_KEY"
MODEL_NAME = "SPECWORKS_MODEL_MODEL"
MODEL_BASE_URL = "SPECWORKS_MODEL_BASE_URL"


class ModelSettingsError(SpecworksError):
    """A model setting is missing or empty; the message names the variable, never a value. Implements REQ-HARNESS-010."""

    def __init__(self, variable: str) -> None:
        super().__init__(f"{variable} is not set")
        self.variable = variable


def model_from_env(env: Mapping[str, str] | None = None) -> BaseChatModel:
    """An OpenAI-compatible chat model from ``env`` (``os.environ`` when None).

    Raises ``ModelSettingsError`` for the first of ``MODEL_KEY``, ``MODEL_NAME`` missing or empty. Implements REQ-HARNESS-010.
    """
    raise NotImplementedError
