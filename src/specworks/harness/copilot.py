"""
GitHub Copilot: the device-flow login, the exchange for a session token that renews itself, and ``log_in``.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from specworks.core.errors import SpecworksError
from specworks.harness.logins import Login, LoginStore, Scope

#: The editor headers Copilot's API expects, also sent with the model's requests.
EDITOR_HEADERS: dict[str, str] = {"Editor-Version": "vscode/1.95.0", "Copilot-Language-Server-Version": "1.246.0"}

#: GitHub's public client id for the device flow (no secret needed).
CLIENT_ID = "Iv1.b507a08c87ecfe98"
DEFAULT_API_BASE = "https://api.githubcopilot.com"
HTTP_TIMEOUT = 15.0
#: Seconds before a session token expires that it is exchanged again.
REFRESH_MARGIN = 60.0
#: How long a session token is trusted when the exchange gives no usable expiry.
FALLBACK_LIFETIME = 1500.0


# @req REQ-HARNESS-011
class CopilotLoginError(SpecworksError):
    """
    The login or the token exchange failed; the message carries a status code at most, never a token.

    ``login_again`` is True when the token was rejected (401/403). Implements REQ-HARNESS-011.
    """

    def __init__(self, message: str, *, login_again: bool = False) -> None:
        super().__init__(message)
        self.login_again = login_again


@contextmanager
def _http(client: httpx.Client | None) -> Iterator[httpx.Client]:
    """
    ``client`` when given, else a client that lives for the block.
    """
    if client is not None:
        yield client
        return
    with httpx.Client(timeout=HTTP_TIMEOUT) as own:
        yield own


def _host(ghe_host: str) -> str:
    """
    A bare host from a GitHub Enterprise host or URL; empty for github.com.
    """
    host = ghe_host.strip().rstrip("/")
    return host.split("://", 1)[1].split("/", 1)[0] if "://" in host else host


def _expiry(value: Any, now: float) -> float:
    """
    The epoch second a session token expires: ``value`` as given by the exchange (epoch or ISO 8601), else a fallback.
    """
    if isinstance(value, bool):
        return now + FALLBACK_LIFETIME
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    return now + FALLBACK_LIFETIME


# @req REQ-HARNESS-012
class CopilotSession:
    """
    The Copilot session token of a login, exchanged on demand and renewed 60 seconds before it expires.

    Implements REQ-HARNESS-012.
    """

    def __init__(self, login: Login, *, client: httpx.Client | None = None, now: Callable[[], float] = time.time) -> None:
        self._login = login
        self._client = client
        self._now = now
        self._lock = threading.Lock()
        self._token = ""
        self._expires_at = 0.0
        self._api_base = DEFAULT_API_BASE

    def _url(self) -> str:
        host = _host(self._login.ghe_host)
        return f"https://{host}/api/v3/copilot_internal/v2/token" if host else "https://api.github.com/copilot_internal/v2/token"

    def _exchange(self) -> None:
        """
        Exchange the OAuth token for a session token. A rejected OAuth token is ``CopilotLoginError(login_again=True)``.
        """
        rejected = False
        with _http(self._client) as client:
            for scheme in ("token", "Bearer"):
                headers = {"Authorization": f"{scheme} {self._login.oauth_token}", "Accept": "application/json", **EDITOR_HEADERS}
                try:
                    response = client.get(self._url(), headers=headers)
                except httpx.HTTPError:
                    raise CopilotLoginError("could not reach GitHub to get a Copilot token") from None
                if response.status_code in (401, 403):
                    rejected = True
                    continue
                if response.status_code != 200:
                    raise CopilotLoginError(f"GitHub refused the Copilot token exchange (status {response.status_code})")
                try:
                    data = response.json()
                    token = data["token"]
                except (ValueError, KeyError, TypeError):
                    raise CopilotLoginError("GitHub's Copilot token exchange gave an unexpected answer") from None
                if not isinstance(token, str) or not token:
                    raise CopilotLoginError("GitHub's Copilot token exchange gave an unexpected answer")
                endpoints = data.get("endpoints")
                api = endpoints.get("api") if isinstance(endpoints, dict) else None
                self._token = token
                self._api_base = api if isinstance(api, str) and api else DEFAULT_API_BASE
                self._expires_at = _expiry(data.get("expires_at"), self._now())
                return
        if rejected:
            raise CopilotLoginError("GitHub no longer accepts the stored Copilot login: run `specworks login copilot` again", login_again=True)
        raise CopilotLoginError("GitHub's Copilot token exchange failed")  # pragma: no cover - the loop always returns or sets rejected

    def token(self) -> str:
        """
        The cached session token, exchanged again when it is within 60 seconds of expiry. Implements REQ-HARNESS-012.
        """
        with self._lock:
            if not self._token or self._now() >= self._expires_at - REFRESH_MARGIN:
                self._exchange()
            return self._token

    @property
    def api_base(self) -> str:
        """
        The API base from the last exchange (``https://api.githubcopilot.com`` when absent). Implements REQ-HARNESS-012.
        """
        return self._api_base

    def default_model(self) -> str | None:
        """
        The id of the model the Copilot API marks as its default chat model, or None when it cannot tell.

        Asks ``<api base>/models`` with the session token. Implements REQ-HARNESS-013.
        """
        raise NotImplementedError


# @req REQ-HARNESS-011
def device_login(
    ghe_host: str,
    prompt: Callable[[str, str], None],
    *,
    client: httpx.Client | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.time,
) -> Login:
    """
    Run GitHub's device flow, calling ``prompt(uri, code)`` once; polls until authorised, denied or expired.

    Raises ``CopilotLoginError``. Implements REQ-HARNESS-011.
    """
    host = _host(ghe_host)
    base = f"https://{host}" if host else "https://github.com"
    accept = {"Accept": "application/json"}
    with _http(client) as http:
        try:
            started = http.post(f"{base}/login/device/code", data={"client_id": CLIENT_ID, "scope": "read:user"}, headers=accept)
            started.raise_for_status()
            info = started.json()
            device_code, uri, code = info["device_code"], info["verification_uri"], info["user_code"]
            interval = float(info.get("interval", 5))
            deadline = now() + float(info.get("expires_in", 900))
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise CopilotLoginError("could not start the GitHub device login") from None
        prompt(uri, code)
        while now() < deadline:
            sleep(interval)
            try:
                polled = http.post(
                    f"{base}/login/oauth/access_token",
                    data={"client_id": CLIENT_ID, "device_code": device_code, "grant_type": "urn:ietf:params:oauth:grant-type:device_code"},
                    headers=accept,
                )
                polled.raise_for_status()
                answer = polled.json()
            except (httpx.HTTPError, ValueError):
                raise CopilotLoginError("could not finish the GitHub device login") from None
            if not isinstance(answer, dict):
                raise CopilotLoginError("could not finish the GitHub device login")
            error = answer.get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval += 5
                continue
            if error == "access_denied":
                raise CopilotLoginError("the GitHub login was denied")
            if error == "expired_token":
                raise CopilotLoginError("the GitHub login code expired")
            if error:
                raise CopilotLoginError(f"the GitHub device login failed ({error})")
            token = answer.get("access_token")
            if not isinstance(token, str) or not token:
                raise CopilotLoginError("could not finish the GitHub device login")
            return Login(token, ghe_host)
    raise CopilotLoginError("the GitHub login code expired")


@dataclass(frozen=True)
class LoginResult:
    """
    Where a login was stored and whether a working one was reused.
    """

    scope: Scope
    reused: bool


# @req REQ-HARNESS-011
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
    """
    Reuse the ``scope`` login when it still exchanges (unless ``force``), else run the device flow and store it.

    Raises ``CopilotLoginError``. Implements REQ-HARNESS-011.
    """
    store = LoginStore() if store is None else store
    existing = None if force else store.load(scope, root)
    if existing is not None:
        try:
            CopilotSession(existing, client=client, now=now).token()
            return LoginResult(scope, True)
        except CopilotLoginError as error:
            if not error.login_again:
                raise
    login = device_login(ghe_host, prompt, client=client, sleep=sleep, now=now)
    store.save(scope, root, login)
    return LoginResult(scope, False)
