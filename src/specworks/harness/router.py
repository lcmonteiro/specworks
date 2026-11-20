"""
The harness's router: chatinho's ``LLMRouter`` on the peers' own model, with ``onboard`` answering whatever it routes to no one.
"""

from __future__ import annotations

from collections.abc import Mapping

from chatinho import ChatMessage
from chatinho.routers import LLMRouter
from chatinho.support.parts.keys.endpoint import Endpoint
from langchain_core.language_models import BaseChatModel

#: The peer that answers a message the model routes to no one.
FALLBACK = "onboard"


class HarnessRouter(LLMRouter):  # type: ignore[misc]
    """
    ``LLMRouter``, with the peer ``fallback`` answering a message it routes to no one. Implements REQ-HARNESS-014.
    """

    def __init__(self, endpoint: Endpoint, *, headers: Mapping[str, str] | None = None, fallback: str = FALLBACK) -> None:
        super().__init__(endpoint, headers=headers)
        self.fallback = fallback

    async def route(self, msg: ChatMessage) -> int | None:
        """
        The peer ``LLMRouter`` chooses, else the peer named ``fallback``. Implements REQ-HARNESS-014.
        """
        raise NotImplementedError


def router_endpoint(model: BaseChatModel) -> tuple[Endpoint, dict[str, str]]:
    """
    The router's endpoint and headers, read off the peers' chat model: its name, base URL, key and headers. Implements REQ-HARNESS-015.
    """
    raise NotImplementedError
