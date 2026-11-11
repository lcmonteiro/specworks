"""GitHub Copilot: the device-flow login, the exchange for a session token that renews itself, and ``log_in``."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import httpx

from specworks.core.errors import SpecworksError
from specworks.harness.logins import Login, LoginStore, Scope

#: The editor headers Copilot's API expects, also sent with the model's requests.
EDITOR_HEADERS: dict[str, str] = {}


class CopilotLoginError(SpecworksError):
    """The login or the token exchange failed; the message carries a status code at most, never a token.

    ``login_again`` is True when the token was rejected (401/403). Implements REQ-HARNESS-011.
    """

    def __init__(self, message: str, *, login_again: bool = False) -> None:
        super().__init__(message)
        self.login_again = login_again


class CopilotSession:
    """The Copilot session token of a login, exchanged on demand and renewed 60 seconds before it expires.

    Implements REQ-HARNESS-012.
    """

    def __init__(self, login: Login, *, client: httpx.Client | None = None, now: Callable[[], float] = time.time) -> None:
        raise NotImplementedError

    def token(self) -> str:
        """The cached session token, exchanged again when it is within 60 seconds of expiry. Implements REQ-HARNESS-012."""
        raise NotImplementedError

    @property
    def api_base(self) -> str:
        """The API base from the last exchange (``https://api.githubcopilot.com`` when absent). Implements REQ-HARNESS-012."""
        raise NotImplementedError


def device_login(
    ghe_host: str,
    prompt: Callable[[str, str], None],
    *,
    client: httpx.Client | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.time,
) -> Login:
    """Run GitHub's device flow, calling ``prompt(uri, code)`` once; polls until authorised, denied or expired.

    Raises ``CopilotLoginError``. Implements REQ-HARNESS-011.
    """
    raise NotImplementedError


@dataclass(frozen=True)
class LoginResult:
    """Where a login was stored and whether a working one was reused."""

    scope: Scope
    reused: bool


def log_in(
    scope: Scope,
    root: Path | None,
    *,
    force: bool,
    ghe_host: str,
    prompt: Callable[[str, str], None],
    store: LoginStore | None = None,
    client: httpx.Client | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.time,
) -> LoginResult:
    """Reuse the ``scope`` login when it still exchanges (unless ``force``), else run the device flow and store it.

    Raises ``CopilotLoginError``. Implements REQ-HARNESS-011.
    """
    raise NotImplementedError
