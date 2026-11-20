"""
The harness's router: chatinho's ``LLMRouter`` on the peers' own model, with ``onboard`` answering whatever it routes to no one.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from typing import cast

from chatinho import ChatMessage, name_of
from chatinho.routers import LLMRouter
from chatinho.support.parts.keys.endpoint import Endpoint
from langchain_core.language_models import BaseChatModel

#: The peer that answers a message the model routes to no one.
FALLBACK = "onboard"


# @req REQ-HARNESS-014
class HarnessRouter(LLMRouter):  # type: ignore[misc]
    """
    ``LLMRouter``, with the peer ``fallback`` answering a message it routes to no one. Implements REQ-HARNESS-014.
    """

    def __init__(self, endpoint: Endpoint, *, headers: Mapping[str, str] | None = None, fallback: str = FALLBACK) -> None:
        super().__init__(endpoint, headers=headers)
        self.fallback = fallback

    async def route(self, msg: ChatMessage) -> int | None:
        """
        The peer ``LLMRouter`` chooses, else the peer named ``fallback`` unless it is the speaker. Implements REQ-HARNESS-014.

        ``everyone``, a name that is no peer, a failed or slow request and no key all come back from ``LLMRouter`` as None.
        """
        chosen: int | None = await super().route(msg)
        if chosen is not None:
            return chosen
        return next((at for at, who in self.peers().items() if name_of(who) == self.fallback and at != msg.frm), None)


# @req REQ-HARNESS-015
def router_endpoint(model: BaseChatModel) -> tuple[Endpoint, dict[str, str]]:
    """
    The router's endpoint and headers, read off the peers' chat model: its name, base URL, key and headers. Implements REQ-HARNESS-015.

    The key is read at each request: a Copilot login's session-token function as it is, so a renewed token is used, and an API key's
    value from its ``SecretStr``. A model that is not OpenAI-compatible gives an endpoint with no key, so every choice falls back.
    """
    from langchain_openai import ChatOpenAI  # here, as model.py does: only building the harness needs it

    if not isinstance(model, ChatOpenAI):
        return Endpoint(), {}
    secret = model.openai_api_key
    key: Callable[[], str] | None
    if secret is None or inspect.iscoroutinefunction(secret):
        key = None  # an async key function cannot be read by the router's key source
    elif callable(secret):
        key = cast("Callable[[], str]", secret)
    else:
        key = secret.get_secret_value
    endpoint = Endpoint(base_url=model.openai_api_base or None, model=model.model_name, api_key=key)
    return endpoint, dict(model.default_headers or {})
