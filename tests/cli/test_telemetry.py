"""Telemetry in the CLI: the events commands record, `telemetry push`, and telemetry in `commit`, `context` and `status`."""

import json
import re
import subprocess

import pytest
from typer.testing import CliRunner

from helpers import REF as PLANNED
from helpers import make_planned_project, make_repo
from specworks.cli import app
from support.commit import REF, run_json
from support.commit import make_project as make_commit_project
from support.langfuse import PUBLIC_KEY, SECRET_KEY, Server, clear_env, event_lines, opt_in, set_keys
from support.modules import make_workspace

runner = CliRunner()
ACTIVE = ".specworks/changes/active"
BASE = {"at", "event", "phase", "ms"}


@pytest.fixture(autouse=True)
def no_langfuse_env(monkeypatch):
    clear_env(monkeypatch)


def lines(folder):
    path = folder / "events.jsonl"
    return path.read_bytes() if path.exists() else b""


def git_out(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


def write_events(folder, count):
    events = [{"at": f"2026-11-03T14:00:{i:02d}Z", "event": "phase", "phase": "design", "ms": 3, "from": "specify", "to": "design"} for i in range(count)]
    (folder / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")


def make_planned(tmp_path, monkeypatch):
    """The planned project opted in, as a git repo on its feature branch."""
    project = make_planned_project(tmp_path, monkeypatch)
    opt_in(project)
    return make_repo(project, monkeypatch)


@pytest.fixture
def opted_in(tmp_path, monkeypatch):
    """The commit project (change `add-login`) opted in, the config committed on the feature branch."""
    root = make_commit_project(tmp_path, monkeypatch)
    opt_in(root)
    subprocess.run(["git", "commit", "-q", "-am", "opt in"], cwd=root, check=True)
    return root


# --- events (REQ-CLI-017) -----------------------------------------------------


# @ac AC-CLI-017.1
def test_ac_cli_017_1_a_failed_gate(tmp_path, monkeypatch):
    planned = make_planned(tmp_path, monkeypatch)
    tasks = planned / ACTIVE / PLANNED / "tasks.md"
    tasks.write_text(tasks.read_text(encoding="utf-8").replace("(REQ-AUTH-002); verify AC-AUTH-002.1 test passes", ""), encoding="utf-8")
    code, data = run_json("gate", "specify", "--change", PLANNED)
    assert code == 1
    failed = [check["name"] for check in data["checks"] if check["blocking"] and not check["ok"]]
    assert len(failed) == 1
    last = event_lines(planned / ACTIVE / PLANNED)[-1]
    assert last["event"] == "gate" and last["gate"] == "specify" and last["passed"] is False
    assert last["failed"] == failed
    assert isinstance(last["ms"], int) and last["ms"] >= 0
    assert set(last) == BASE | {"gate", "passed", "failed"}


# @ac AC-CLI-017.2
def test_ac_cli_017_2_each_commands_event(tmp_path, monkeypatch):
    planned = make_planned(tmp_path, monkeypatch)
    counts: dict[str, int] = {}

    def step(folder_of, event, fields, *args):
        """Run ``args``; the change's folder (``folder_of(data)``) gains exactly one ``event`` event with ``fields``."""
        code, data = run_json(*args)
        assert code == 0, data
        folder = folder_of(data)
        ref = args[args.index("--change") + 1] if "--change" in args else args[1]
        before = counts.get(ref, 0)
        events = event_lines(folder)
        assert len(events) == before + 1, (args, events)
        assert events[-1]["event"] == event
        assert set(events[-1]) == BASE | fields, (args, events[-1])
        assert isinstance(events[-1]["ms"], int)
        counts[ref] = len(events)
        return data, events[-1]

    other = lambda data: planned / ACTIVE / "add-other"  # noqa: E731
    main = lambda data: planned / ACTIVE / PLANNED  # noqa: E731

    step(other, "new", set(), "new", "add-other", "--no-branch")
    _, event = step(other, "run", {"key", "exitCode"}, "run", "test", "--change", "add-other")
    assert event["key"] == "test" and event["exitCode"] == 0
    _, event = step(other, "finding", {"action", "id", "type", "step"}, "finding", "add", "code-gap", "x", "--proposal", "y", "--change", "add-other")
    assert event["action"] == "add" and event["type"] == "code-gap"
    _, event = step(other, "cycle", {"phases", "open"}, "cycle", "--change", "add-other")
    assert event["open"] == 1
    _, event = step(other, "start", {"to", "started"}, "start", "specify", "--change", "add-other")
    assert event["to"] == "specify" and event["started"] is True

    (planned / ACTIVE / PLANNED / "review.md").write_text("# Review\n\n## Findings\n\nNone.\n", encoding="utf-8")
    _, event = step(main, "phase", {"from", "to"}, "phase", "review", "--change", PLANNED)
    assert event["to"] == "review"
    data, event = step(main, "commit", {"committed", "made"}, "commit", "--change", PLANNED)
    assert event["made"] is True and event["committed"] == len(data["committed"])
    data, event = step(main, "validate", {"verdict", "critical", "warnings"}, "validate", "--change", PLANNED, "--base", "main")
    assert event["verdict"] == data["verdict"] == "PASS"
    step(main, "phase", {"from", "to"}, "phase", "validate", "--change", PLANNED)
    step(main, "phase", {"from", "to"}, "phase", "close", "--change", PLANNED)
    data, event = step(lambda data: planned / data["archivedTo"], "close", {"merged"}, "close", "--change", PLANNED, "--base", "main")
    assert event["merged"] == 1
    step(lambda data: planned / data["path"], "abandon", set(), "abandon", "--change", "add-other", "--reason", "not needed")


# @ac AC-CLI-017.3
def test_ac_cli_017_3_no_content(tmp_path, monkeypatch):
    planned = make_planned(tmp_path, monkeypatch)
    assert run_json("new", "add-other", "--no-branch")[0] == 0
    assert run_json("finding", "add", "code-gap", "secret text", "--proposal", "other text", "--change", "add-other")[0] == 0
    code, data = run_json("abandon", "--change", "add-other", "--reason", "why text")
    assert code == 0, data
    text = (planned / data["path"] / "events.jsonl").read_text(encoding="utf-8")
    assert len(text.splitlines()) >= 3
    for secret in ("secret text", "other text", "why text"):
        assert secret not in text


# @ac AC-CLI-017.4
def test_ac_cli_017_4_a_refused_command(tmp_path, monkeypatch):
    planned = make_planned(tmp_path, monkeypatch)
    folder = planned / ACTIVE / PLANNED
    assert run_json("phase", "design", "--change", PLANNED)[0] == 0
    before = lines(folder)
    assert before
    code, data = run_json("phase", "nowhere", "--change", PLANNED)
    assert code == 1 and "error" in data
    assert lines(folder) == before


# @ac AC-CLI-017.5
def test_ac_cli_017_5_telemetry_off(tmp_path, monkeypatch):
    root = make_repo(make_planned_project(tmp_path, monkeypatch), monkeypatch)
    assert run_json("new", "add-other", "--no-branch")[0] == 0
    run_json("gate", "specify", "--change", PLANNED)
    assert run_json("phase", "design", "--change", PLANNED)[0] == 0
    assert run_json("commit", "--change", PLANNED)[0] == 0
    assert list(root.rglob("events.jsonl")) == []


# --- commit (REQ-CLI-012) -----------------------------------------------------


# @ac AC-CLI-012.5
def test_ac_cli_012_5_events_sent_after_the_commit(opted_in, monkeypatch):
    folder = opted_in / ACTIVE / REF
    assert run_json("phase", "design", "--change", REF)[0] == 0
    with Server() as server:
        set_keys(monkeypatch, server.url)
        code, data = run_json("commit", "--change", REF)
    assert code == 0, data
    shown = git_out(opted_in, "show", "--name-only", "--format=", "HEAD").split()
    assert not any(path.endswith(("events.jsonl", "events.sent")) for path in shown), shown
    events = event_lines(folder)
    assert events[-1]["event"] == "commit"
    assert data["telemetry"] == {"sent": len(events), "queued": 0, "reason": None}
    assert sum(1 for batch in server.batches() for item in batch if item["type"] != "trace-create") == len(events)


# @ac AC-CLI-012.6
def test_ac_cli_012_6_langfuse_unreachable(opted_in, monkeypatch):
    head = git_out(opted_in, "rev-parse", "HEAD")
    assert run_json("phase", "design", "--change", REF)[0] == 0
    with Server([500]) as server:
        set_keys(monkeypatch, server.url)
        result = runner.invoke(app, ["commit", "--change", REF])
    assert result.exit_code == 0, result.output
    assert git_out(opted_in, "rev-parse", "HEAD") != head
    queued = len(event_lines(opted_in / ACTIVE / REF))
    assert "specworks telemetry push" in result.output
    assert "queued" in result.output and str(queued) in result.output
    assert "500" in result.output


# @ac AC-CLI-012.7
def test_ac_cli_012_7_telemetry_not_on(tmp_path, monkeypatch):
    root = make_commit_project(tmp_path, monkeypatch)
    assert run_json("phase", "design", "--change", REF)[0] == 0
    with Server() as server:
        set_keys(monkeypatch, server.url)
        code, data = run_json("commit", "--change", REF)
    assert code == 0, data
    assert data["telemetry"] is None
    assert server.requests == []
    assert list(root.rglob("events.jsonl")) == []


# --- telemetry push (REQ-CLI-018) --------------------------------------------


# @ac AC-CLI-018.1
def test_ac_cli_018_1_sent(opted_in, monkeypatch):
    write_events(opted_in / ACTIVE / REF, 3)
    with Server() as server:
        set_keys(monkeypatch, server.url)
        code, data = run_json("telemetry", "push", "--change", REF)
    assert code == 0, data
    assert (data["sent"], data["queued"], data["reason"]) == (3, 0, None)
    assert len(server.requests) == 1


# @ac AC-CLI-018.2
def test_ac_cli_018_2_still_queued(opted_in, monkeypatch):
    write_events(opted_in / ACTIVE / REF, 3)
    with Server([500]) as server:
        set_keys(monkeypatch, server.url)
        code, data = run_json("telemetry", "push", "--change", REF)
    assert code == 1
    assert (data["sent"], data["queued"]) == (0, 3) and "500" in data["reason"]


# @ac AC-CLI-018.3
@pytest.mark.parametrize("state", ["off", "keys missing"])
def test_ac_cli_018_3_not_configured(tmp_path, monkeypatch, state):
    root = make_commit_project(tmp_path, monkeypatch)
    if state == "keys missing":
        opt_in(root)
    write_events(root / ACTIVE / REF, 3)
    with Server() as server:
        set_keys(monkeypatch, server.url)
        if state == "keys missing":
            monkeypatch.delenv("SPECWORKS_LANGFUSE_SECRET_KEY")
        code, data = run_json("telemetry", "push", "--change", REF)
    assert code == 1 and set(data) == {"error"}
    assert ("off" in data["error"]) if state == "off" else ("SPECWORKS_LANGFUSE_SECRET_KEY" in data["error"])
    assert server.requests == []


# --- context and status (REQ-CLI-004, REQ-CLI-019) ---------------------------


# @ac AC-CLI-004.7
def test_ac_cli_004_7_telemetry_state(tmp_path, monkeypatch):
    root = make_commit_project(tmp_path, monkeypatch)
    config = root / ".specworks/config.yml"
    plain = config.read_text(encoding="utf-8")
    opt_in(root)
    set_keys(monkeypatch)
    states = []
    for step in ("on", "keys missing", "off"):
        if step == "keys missing":
            monkeypatch.delenv("SPECWORKS_LANGFUSE_SECRET_KEY")
        if step == "off":
            config.write_text(plain, encoding="utf-8")
        result = runner.invoke(app, ["context", "--json"])
        assert result.exit_code == 0, result.output
        assert PUBLIC_KEY not in result.output and SECRET_KEY not in result.output
        telemetry = json.loads(result.output)["telemetry"]
        states.append(telemetry["state"])
        assert telemetry["host"] == "https://cloud.langfuse.com"
    assert states == ["on", "keys missing", "off"]


# @ac AC-CLI-019.1
def test_ac_cli_019_1_the_ids(tmp_path, monkeypatch):
    make_commit_project(tmp_path, monkeypatch)
    code, before = run_json("status", "--change", REF)
    assert code == 0, before
    assert run_json("abandon", "--change", REF, "--reason", "not needed")[0] == 0
    code, after = run_json("status", "--change", REF)
    assert code == 0, after
    assert before["telemetry"]["sessionId"] == after["telemetry"]["sessionId"] == "add-login"
    assert before["telemetry"]["traceId"] == after["telemetry"]["traceId"]
    assert len(before["telemetry"]["traceId"]) == 32


# @ac AC-CLI-019.2
def test_ac_cli_019_2_a_change_in_a_module(tmp_path, monkeypatch):
    root = make_workspace(tmp_path, monkeypatch)
    assert run_json("new", "cleanup", "--no-branch")[0] == 0
    assert run_json("new", "cleanup", "--module", "billing", "--no-branch")[0] == 0
    for meta in (root / ".specworks/changes/active/cleanup/.change.yaml", root / "services/billing/.specworks/changes/active/cleanup/.change.yaml"):
        text = meta.read_text(encoding="utf-8")
        meta.write_text(re.sub(r"(?m)^created: .*$", "created: '2026-11-03T10:00:00'", text), encoding="utf-8")  # created at the same time
    code, module = run_json("status", "--change", "billing:cleanup")
    assert code == 0, module
    code, top = run_json("status", "--change", "cleanup")
    assert code == 0, top
    assert module["telemetry"]["sessionId"] == "billing:cleanup"
    assert top["telemetry"]["sessionId"] == "cleanup"
    assert module["telemetry"]["traceId"] != top["telemetry"]["traceId"]
