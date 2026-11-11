"""The Copilot login: the device flow, its scopes, reuse, and no token shown (REQ-HARNESS-011), on a fake GitHub with no network and no waiting."""

import logging
import os
import traceback
from functools import cached_property

import pytest

from specworks.harness.copilot import CopilotLoginError, CopilotSession, LoginResult, log_in
from specworks.harness.logins import Login, LoginStore
from support.copilot import Clock, FakeGitHub

OAUTH = "gho_secret"
SESSION = "tid=secret"


class Flow:
    """A login run against a fake GitHub, a store in a temporary folder and a clock that sleeps by advancing."""

    def __init__(self, tmp_path, **github):
        self.base = tmp_path / "config"
        self.clock = Clock()
        self.github = FakeGitHub(now=self.clock.time, **github)
        self.prompts: list[tuple[str, str]] = []
        self.a = tmp_path / "a"
        self.b = tmp_path / "b"
        self.a.mkdir()
        self.b.mkdir()

    def sleep(self, seconds):
        assert self.clock.time() < Clock().time() + 3600, "the flow waits for ever: it has no deadline"
        self.clock.sleep(seconds)

    @cached_property
    def store(self):
        return LoginStore(self.base)

    def prompt(self, uri, code):
        self.prompts.append((uri, code))

    def log_in(self, scope="global", root=None, *, force=False, ghe_host="") -> LoginResult:
        return log_in(
            scope,
            root,
            force=force,
            ghe_host=ghe_host,
            prompt=self.prompt,
            store=self.store,
            client=self.github.client(),
            sleep=self.sleep,
            now=self.clock.time,
        )


@pytest.fixture
def flow(tmp_path):
    return Flow(tmp_path)


def stored_files(flow):
    return [p for p in flow.base.rglob("*") if p.is_file()]


def snapshot(flow):
    return {str(p): p.read_bytes() for p in stored_files(flow)}


# @ac AC-HARNESS-011.1
def test_ac_harness_011_1_a_global_login(flow):
    flow.github.polls = ["pending", "slow_down", "authorize"]
    result = flow.log_in("global")
    assert result == LoginResult(scope="global", reused=False)
    assert flow.prompts == [("https://github.com/login/device", "ABCD-1234")]
    token = flow.github.authorized[0]
    assert flow.store.load("global", None) == Login(token)
    # a project in any folder finds it
    assert flow.store.find(flow.a) == Login(token)
    assert flow.store.find(flow.b) == Login(token)
    assert flow.store.find(None) == Login(token)
    files = stored_files(flow)
    assert files
    if os.name != "nt":  # the permission bits are not enforced on Windows
        assert all(p.stat().st_mode & 0o077 == 0 for p in files)
    assert all(SESSION not in p.read_text(encoding="utf-8") for p in files), "only the OAuth token is kept"


# @ac AC-HARNESS-011.2
def test_ac_harness_011_2_a_local_login(flow):
    result = flow.log_in("local", flow.a)
    assert result == LoginResult(scope="local", reused=False)
    token = flow.github.authorized[0]
    assert flow.store.find(flow.a) == Login(token)
    assert flow.store.load("local", flow.a) == Login(token)
    assert flow.store.find(flow.b) is None
    assert flow.store.load("global", None) is None
    assert list(flow.a.rglob("*")) == [], "no file is written inside the project"
    assert stored_files(flow)


# @ac AC-HARNESS-011.3
def test_ac_harness_011_3_an_existing_login_is_reused(flow):
    flow.github.valid.add(OAUTH)
    flow.store.save("global", None, Login(OAUTH))
    before = snapshot(flow)
    result = flow.log_in("global")
    assert result == LoginResult(scope="global", reused=True)
    assert flow.github.device_flows() == 0
    assert flow.prompts == []
    assert flow.store.load("global", None) == Login(OAUTH)
    assert snapshot(flow) == before


# @ac AC-HARNESS-011.4
def test_ac_harness_011_4_a_forced_login(flow):
    flow.github.valid.add(OAUTH)
    flow.store.save("global", None, Login(OAUTH))
    result = flow.log_in("global", force=True)
    assert result == LoginResult(scope="global", reused=False)
    assert flow.github.device_flows() == 1
    assert flow.prompts
    assert flow.store.load("global", None) == Login(flow.github.authorized[0])
    assert flow.store.load("global", None) != Login(OAUTH)


# @ac AC-HARNESS-011.5
def test_ac_harness_011_5_a_stale_login(flow):
    flow.store.save("global", None, Login(OAUTH))  # GitHub does not accept it
    result = flow.log_in("global")
    assert result == LoginResult(scope="global", reused=False)
    assert flow.github.device_flows() == 1
    assert flow.store.load("global", None) == Login(flow.github.authorized[0])


# @ac AC-HARNESS-011.6
@pytest.mark.parametrize("ending", ["denied", "expired", "never authorised"])
def test_ac_harness_011_6_a_flow_that_does_not_finish(flow, ending):
    flow.github.valid.add(OAUTH)
    flow.store.save("global", None, Login(OAUTH))
    before = snapshot(flow)
    flow.github.polls = [] if ending == "never authorised" else ["pending", ending]
    with pytest.raises(CopilotLoginError):
        flow.log_in("global", force=True)
    assert flow.store.load("global", None) == Login(OAUTH)
    assert snapshot(flow) == before
    assert flow.github.authorized == []


# @ac AC-HARNESS-011.7
def test_ac_harness_011_7_github_enterprise(flow):
    host = "example.ghe.com"
    flow.log_in("global", ghe_host=host)
    assert flow.github.device_flows() == 1
    assert all(h == host or h.endswith("." + host) for h in flow.github.hosts()), flow.github.hosts()
    stored = flow.store.load("global", None)
    assert stored is not None and stored.ghe_host == host
    # every later token exchange goes to that host too
    before = len(flow.github.requests)
    CopilotSession(stored, client=flow.github.client(), now=flow.clock.time).token()
    later = flow.github.requests[before:]
    assert later and all(r.url.host == host or r.url.host.endswith("." + host) for r in later)


def run_and_collect(flow, capsys, caplog, run):
    """Everything a run shows: its output, log lines, result, error and the error's traceback."""
    shown = []
    with caplog.at_level(logging.DEBUG):
        try:
            shown.append(repr(run()))
        except CopilotLoginError as error:
            shown += [str(error), repr(error), "".join(traceback.format_exception(error))]
    out = capsys.readouterr()
    shown += [out.out, out.err, caplog.text, *(part for prompt in flow.prompts for part in prompt), *(r.getMessage() for r in caplog.records)]
    return "\n".join(shown)


# @ac AC-HARNESS-011.8
@pytest.mark.parametrize("ending", ["authorised", "denied", "stale and denied"])
def test_ac_harness_011_8_no_token_shown(flow, capsys, caplog, ending):
    flow.github.valid.add(OAUTH)
    flow.store.save("global", None, Login(OAUTH))
    flow.github.polls = ["authorize"] if ending == "authorised" else ["denied"]
    force = ending != "stale and denied"
    if ending == "stale and denied":
        flow.github.valid.discard(OAUTH)  # the stored login is rejected, and its flow is then denied
    shown = run_and_collect(flow, capsys, caplog, lambda: flow.log_in("global", force=force))
    assert "gho_secret" not in shown
    assert SESSION not in shown
    assert repr(Login(OAUTH)) and OAUTH not in repr(Login(OAUTH))


# @ac AC-HARNESS-011.8
def test_ac_harness_011_8_a_reused_login_shows_no_token(flow, capsys, caplog):
    flow.github.valid.add(OAUTH)
    flow.store.save("global", None, Login(OAUTH))
    shown = run_and_collect(flow, capsys, caplog, lambda: flow.log_in("global"))
    assert "gho_secret" not in shown and SESSION not in shown
    session = CopilotSession(Login(OAUTH), client=flow.github.client(), now=flow.clock.time)
    session.token()
    assert OAUTH not in repr(session) and SESSION not in repr(session)
