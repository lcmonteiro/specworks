"""A fake GitHub for the Copilot login tests: the device flow and the session-token exchange, on a fake transport with no network.

Requests are told apart by their path, so the host (github.com or a GitHub Enterprise one) is free; every request is recorded in ``requests``.
"""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field

import httpx

DEFAULT_API = "https://api.individual.githubcopilot.com"
SESSION_LIFE = 25 * 60


@dataclass
class Clock:
    """A clock that only moves when a test sleeps or advances it."""

    at: float = 1_000_000.0

    def time(self) -> float:
        return self.at

    def sleep(self, seconds: float) -> None:
        self.at += seconds

    def advance(self, seconds: float) -> None:
        self.at += seconds


@dataclass
class FakeGitHub:
    """What the login tests need from GitHub.

    ``valid`` is the set of OAuth tokens that exchange for a session token; ``polls`` is what the device flow's access-token polls answer, in order
    (``authorize``, ``pending``, ``slow_down``, ``denied`` or ``expired``; ``pending`` once the list runs out). ``authorize`` registers a new OAuth
    token (``gho_secret_new<n>``) as valid. Every session token is unique: ``tid=secret<n>``.
    """

    now: Callable[[], float] = field(default_factory=lambda: Clock().time)
    valid: set[str] = field(default_factory=set)
    polls: list[str] = field(default_factory=lambda: ["authorize"])
    api: str | None = DEFAULT_API
    interval: int = 5
    expires_in: int = 900
    life: int = SESSION_LIFE
    requests: list[httpx.Request] = field(default_factory=list)
    authorized: list[str] = field(default_factory=list)
    sessions: dict[str, list[str]] = field(default_factory=dict)

    def client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self.handle))

    def paths(self) -> list[str]:
        return [r.url.path for r in self.requests]

    def hosts(self) -> set[str]:
        return {r.url.host for r in self.requests}

    def device_flows(self) -> int:
        return sum(1 for p in self.paths() if p.endswith("/login/device/code"))

    def exchanges(self) -> int:
        return sum(1 for p in self.paths() if p.endswith("/copilot_internal/v2/token"))

    def last_session(self, oauth_token: str) -> str:
        return self.sessions[oauth_token][-1]

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if path.endswith("/login/device/code"):
            return httpx.Response(
                200,
                json={
                    "device_code": "dc-1",
                    "user_code": "ABCD-1234",
                    "verification_uri": f"https://{request.url.host}/login/device",
                    "expires_in": self.expires_in,
                    "interval": self.interval,
                },
            )
        if path.endswith("/login/oauth/access_token"):
            return self.poll()
        if path.endswith("/copilot_internal/v2/token"):
            return self.exchange(request)
        return httpx.Response(404, json={"message": "Not Found"})

    def poll(self) -> httpx.Response:
        step = self.polls.pop(0) if self.polls else "pending"
        if step == "authorize":
            token = f"gho_secret_new{len(self.authorized) + 1}"
            self.authorized.append(token)
            self.valid.add(token)
            return httpx.Response(200, json={"access_token": token, "token_type": "bearer", "scope": "read:user"})
        error = {"pending": "authorization_pending", "slow_down": "slow_down", "denied": "access_denied", "expired": "expired_token"}[step]
        return httpx.Response(200, json={"error": error})

    def exchange(self, request: httpx.Request) -> httpx.Response:
        oauth_token = request.headers.get("authorization", "").split()[-1]
        if oauth_token not in self.valid:
            # An API that echoes the credential it rejects: no error may repeat it.
            return httpx.Response(401, json={"message": f"Bad credentials: {oauth_token}"})
        issued = self.sessions.setdefault(oauth_token, [])
        token = f"tid=secret{sum(len(v) for v in self.sessions.values()) + 1}"
        issued.append(token)
        body: dict = {"token": token, "expires_at": int(self.now()) + self.life, "refresh_in": self.life - 300}
        if self.api is not None:
            body["endpoints"] = {"api": self.api}
        return httpx.Response(200, content=json.dumps(body), headers={"content-type": "application/json"})


def real_clock_github(**kwargs) -> FakeGitHub:
    """A fake GitHub that reads the real time, for commands that cannot be given a clock; its poll interval is 0 so nothing waits."""
    return FakeGitHub(now=time.time, interval=0, **kwargs)


def route_httpx_to(monkeypatch, github: FakeGitHub) -> None:
    """Send every request httpx makes, from any client, to ``github``."""
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", lambda self, request: github.handle(request))
