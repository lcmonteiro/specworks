"""
The Copilot session token: exchanged from the stored login, renewed before it expires, and a revoked login (REQ-HARNESS-012).
"""

import traceback

import pytest

from specworks.core.errors import SpecworksError
from specworks.harness import model_from_env
from specworks.harness.copilot import CopilotLoginError, CopilotSession
from specworks.harness.logins import Login, LoginStore
from specworks.harness.model import MODEL_NAME
from support.copilot import Clock, FakeGitHub

OAUTH = "gho_secret"
MINUTE = 60


def session_of(github, clock, token=OAUTH):
    return CopilotSession(Login(token), client=github.client(), now=clock.time)


# @ac AC-HARNESS-012.4
def test_ac_harness_012_4_a_long_chat():
    clock = Clock()
    github = FakeGitHub(now=clock.time, valid={OAUTH}, life=25 * MINUTE)
    session = session_of(github, clock)
    first = session.token()
    assert github.exchanges() == 1
    clock.advance(10 * MINUTE)
    assert session.token() == first and github.exchanges() == 1, "a token that is still good is reused"
    clock.advance(16 * MINUTE)  # 26 minutes: the first token has expired
    second = session.token()
    assert second != first
    assert second == github.last_session(OAUTH)
    assert github.exchanges() == 2
    assert github.device_flows() == 0, "no login is needed"


# @ac AC-HARNESS-012.4
def test_ac_harness_012_4_renewed_before_it_expires():
    clock = Clock()
    github = FakeGitHub(now=clock.time, valid={OAUTH}, life=25 * MINUTE)
    session = session_of(github, clock)
    first = session.token()
    clock.advance(25 * MINUTE - 30)  # still valid for 30 seconds, but inside the 60 seconds before expiry
    assert session.token() != first
    assert github.exchanges() == 2


# @ac AC-HARNESS-012.5
def test_ac_harness_012_5_a_login_that_no_longer_works():
    clock = Clock()
    github = FakeGitHub(now=clock.time)  # GitHub rejects every token
    session = session_of(github, clock, "gho_secret_revoked")
    with pytest.raises(CopilotLoginError) as error:
        session.token()
    assert error.value.login_again is True
    assert "specworks login copilot" in str(error.value)
    shown = "\n".join([str(error.value), repr(error.value), "".join(traceback.format_exception(error.value))])
    assert "gho_secret" not in shown and "tid=secret" not in shown


# @ac AC-HARNESS-012.5
def test_ac_harness_012_5_known_before_the_session_starts(tmp_path):
    clock = Clock()
    github = FakeGitHub(now=clock.time)
    store = LoginStore(tmp_path / "config")
    store.save("global", None, Login("gho_secret_revoked"))
    with pytest.raises(SpecworksError) as error:
        model_from_env({MODEL_NAME: "gpt-test"}, root=tmp_path, store=store, client=github.client())
    assert "specworks login copilot" in str(error.value)
    shown = "\n".join([str(error.value), repr(error.value), "".join(traceback.format_exception(error.value))])
    assert "gho_secret" not in shown
