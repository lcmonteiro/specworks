"""The Langfuse client: telemetry settings and sending a change's unsent events."""

import base64
import json
import time

import pytest

from specworks.core.changes import Change
from specworks.core.config import TelemetryConfig
from specworks.tools.langfuse import DEFAULT_HOST, LangfuseSettings, langfuse_settings, send_events
from support.langfuse import PUBLIC_KEY, SECRET_KEY, Server, Silent

KEYS = {"SPECWORKS_LANGFUSE_PUBLIC_KEY": PUBLIC_KEY, "SPECWORKS_LANGFUSE_SECRET_KEY": SECRET_KEY}
TRACE = "0123456789abcdef0123456789abcdef"
REF = "add-login"


def make_change(tmp_path, lines=0, sent=None):
    """A change folder with ``lines`` events in events.jsonl and, unless None, ``sent`` in events.sent."""
    folder = tmp_path / REF
    folder.mkdir()
    change = Change(name=REF, path=folder, phase="implement", created="2026-11-03T10:00:00")
    change.save()
    if lines:
        events = [
            {"at": f"2026-11-03T14:{i // 60:02d}:{i % 60:02d}Z", "event": "gate", "phase": "implement", "ms": 900 + i, "gate": "test", "passed": i % 2 == 0}
            for i in range(lines)
        ]
        (folder / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    if sent is not None:
        (folder / "events.sent").write_text(f"{sent}\n", encoding="utf-8")
    return change


def sent_count(change):
    path = change.path / "events.sent"
    return int(path.read_text(encoding="utf-8").strip()) if path.is_file() else 0


def settings(host):
    return LangfuseSettings(state="on", host=host, public_key=PUBLIC_KEY, secret_key=SECRET_KEY)


def send(change, host):
    return send_events(change, settings(host), TRACE, REF, "(top)")


# --- settings (REQ-INTEG-008) -------------------------------------------------


# @ac AC-INTEG-008.1
def test_ac_integ_008_1_on():
    result = langfuse_settings(TelemetryConfig(langfuse=True), env=dict(KEYS))
    assert result.state == "on" and result.host == DEFAULT_HOST == "https://cloud.langfuse.com"
    assert result.public_key == PUBLIC_KEY and result.secret_key == SECRET_KEY
    assert PUBLIC_KEY not in repr(result) and SECRET_KEY not in repr(result)


# @ac AC-INTEG-008.2
@pytest.mark.parametrize("env", [{"SPECWORKS_LANGFUSE_PUBLIC_KEY": PUBLIC_KEY}, {**KEYS, "SPECWORKS_LANGFUSE_SECRET_KEY": ""}], ids=["unset", "empty"])
def test_ac_integ_008_2_keys_missing(env):
    result = langfuse_settings(TelemetryConfig(langfuse=True), env=env)
    assert result.state == "keys missing"
    assert "SPECWORKS_LANGFUSE_SECRET_KEY" in result.missing


# @ac AC-INTEG-008.3
@pytest.mark.parametrize("config", [None, TelemetryConfig(langfuse=False)], ids=["no block", "false"])
def test_ac_integ_008_3_not_opted_in(config):
    assert langfuse_settings(config, env=dict(KEYS)).state == "off"


# @ac AC-INTEG-008.4
def test_ac_integ_008_4_the_host():
    config = TelemetryConfig(langfuse=True, host="https://a.example.com")
    assert langfuse_settings(config, env={**KEYS, "SPECWORKS_LANGFUSE_HOST": "https://b.example.com"}).host == "https://b.example.com"
    assert langfuse_settings(config, env=dict(KEYS)).host == "https://a.example.com"


# @ac AC-INTEG-008.5
def test_ac_integ_008_5_the_plain_langfuse_variables_are_ignored():
    env = {"LANGFUSE_PUBLIC_KEY": PUBLIC_KEY, "LANGFUSE_SECRET_KEY": SECRET_KEY, "LANGFUSE_HOST": "https://b.example.com"}
    result = langfuse_settings(TelemetryConfig(langfuse=True, host="https://a.example.com"), env=env)
    assert result.state == "keys missing" and result.host == "https://a.example.com"


# --- sending (REQ-INTEG-009) --------------------------------------------------


# @ac AC-INTEG-009.1
def test_ac_integ_009_1_only_the_unsent_events(tmp_path):
    change = make_change(tmp_path, lines=5, sent=3)
    lines = (change.path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    with Server() as server:
        result = send(change, server.url)
    assert (result.sent, result.queued, result.reason) == (2, 0, None)
    assert sent_count(change) == 5
    assert len(server.requests) == 1
    request = server.requests[0]
    assert request["path"] == "/api/public/ingestion"
    assert request["authorization"] == "Basic " + base64.b64encode(f"{PUBLIC_KEY}:{SECRET_KEY}".encode()).decode()
    trace, *spans = request["body"]["batch"]
    assert trace["type"] == "trace-create" and trace["body"]["id"] == TRACE and trace["body"]["name"] == REF and trace["body"]["sessionId"] == REF
    assert len(spans) == 2
    for span, line in zip(spans, lines[3:], strict=True):
        event = json.loads(line)
        assert span["body"]["traceId"] == TRACE and span["body"]["name"] == event["event"] and span["body"]["endTime"] == event["at"]
        assert span["body"]["metadata"]["gate"] == event["gate"] and span["body"]["metadata"]["passed"] == event["passed"]


# @ac AC-INTEG-009.2
def test_ac_integ_009_2_the_server_refuses(tmp_path):
    change = make_change(tmp_path, lines=4)
    with Server([500]) as server:
        result = send(change, server.url)
    assert (result.sent, result.queued) == (0, 4) and "500" in (result.reason or "")
    assert not (change.path / "events.sent").exists()


# @ac AC-INTEG-009.3
def test_ac_integ_009_3_no_answer(tmp_path):
    change = make_change(tmp_path, lines=3, sent=1)
    with Silent() as host:
        started = time.monotonic()
        result = send(change, host.url)
        elapsed = time.monotonic() - started
    assert elapsed < 7, elapsed
    assert (result.sent, result.queued) == (0, 2)
    assert "timed out" in (result.reason or "").lower() or "timeout" in (result.reason or "").lower(), result.reason
    assert sent_count(change) == 1


# @ac AC-INTEG-009.4
@pytest.mark.parametrize("lines, sent", [(3, 3), (0, None)], ids=["all sent", "no log"])
def test_ac_integ_009_4_nothing_to_send(tmp_path, lines, sent):
    change = make_change(tmp_path, lines=lines, sent=sent)
    with Server() as server:
        result = send(change, server.url)
    assert server.requests == []
    assert (result.sent, result.queued) == (0, 0)


# @ac AC-INTEG-009.5
def test_ac_integ_009_5_many_events(tmp_path):
    change = make_change(tmp_path, lines=250)
    with Server([200, 200, 500]) as server:
        result = send(change, server.url)
    spans = [[item for item in batch if item["type"] != "trace-create"] for batch in server.batches()]
    assert [len(batch) for batch in spans] == [100, 100, 50]
    assert sent_count(change) == 200
    assert (result.sent, result.queued) == (200, 50)


# @ac AC-INTEG-009.6
def test_ac_integ_009_6_the_keys_stay_secret(tmp_path):
    change = make_change(tmp_path, lines=2)
    with Server([401]) as server:
        result = send(change, server.url)
    assert "401" in (result.reason or "")
    assert PUBLIC_KEY not in result.reason and SECRET_KEY not in result.reason
