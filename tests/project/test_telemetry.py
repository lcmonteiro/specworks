"""
Telemetry in the project: the config block, the change's event log and its trace identity.
"""

import json
import re
import subprocess

import pytest

from specworks.core.changes import Change, archived_as, load_change, set_phase
from specworks.core.config import TelemetryConfig, load_config
from specworks.core.config_file import set_config_value
from specworks.core.errors import ConfigError
from specworks.core.events import record_event, session_id, trace_id
from specworks.specs.merge import archive_change
from support.config_set import CONFIG, entries, invoke, make_project, read
from support.langfuse import event_lines, opt_in
from support.modules import make_workspace, run_json

REF = "add-login"


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


def write(root, text):
    (root / CONFIG).write_text(text, encoding="utf-8")


def add_change(root, phase="specify"):
    result = invoke("new", REF, "--no-branch")
    assert result.exit_code == 0, result.output
    change = load_change(load_config(root), REF)
    set_phase(change, phase)
    return change


def enabled(root):
    telemetry = load_config(root).telemetry
    return bool(telemetry and telemetry.langfuse)


def comments(text):
    return [line for line in text.splitlines() if line.lstrip().startswith("#")]


# --- the config block (REQ-PROJ-003) -----------------------------------------


# @ac AC-PROJ-003.9
@pytest.mark.parametrize(
    "block, named",
    [
        ("telemetry: true\n", "telemetry"),
        ("telemetry:\n  langfuse: true\n  secret_key: sk-test\n", "telemetry"),
        ("telemetry:\n  langfuse: maybe\n", "telemetry.langfuse"),
        ('telemetry:\n  langfuse: true\n  host: "cloud.langfuse.com"\n', "telemetry.host"),
    ],
    ids=["not a mapping", "another key", "not a boolean", "no scheme"],
)
def test_ac_proj_003_9_telemetry_refused(project, block, named):
    write(project, read(project) + block)
    with pytest.raises(ConfigError) as error:
        load_config(project)
    assert named in str(error.value)


# @ac AC-PROJ-003.9
def test_ac_proj_003_9_telemetry_loads(project):
    write(project, read(project) + 'telemetry: {langfuse: true, host: "http://localhost:3000"}\n')
    assert load_config(project).telemetry == TelemetryConfig(langfuse=True, host="http://localhost:3000")


# @ac AC-PROJ-003.10
def test_ac_proj_003_10_telemetry_in_a_module(tmp_path, monkeypatch):
    make_workspace(tmp_path, monkeypatch)
    billing = tmp_path / "services/billing"
    opt_in(billing)
    code, data = run_json("context")
    assert code == 1 and "'telemetry'" in data["error"] and "top level" in data["error"], data


# --- set_config_value (REQ-PROJ-032, REQ-PROJ-025) -----------------------------


# @ac AC-PROJ-032.1
def test_ac_proj_032_1_opting_in_with_a_host(project):
    before = read(project)
    set_config_value(project, "telemetry.langfuse", "true")
    set_config_value(project, "telemetry.host", "https://langfuse.example.com")
    text = read(project)
    assert load_config(project).telemetry == TelemetryConfig(langfuse=True, host="https://langfuse.example.com")
    assert len(entries(text, "telemetry")) == 1
    assert len(entries(text, "langfuse")) == 1 and len(entries(text, "host")) == 1
    assert comments(before) and all(line in text.splitlines() for line in comments(before))


# @ac AC-PROJ-032.2
def test_ac_proj_032_2_replaced_and_cleared(project):
    write(project, read(project) + "telemetry:\n  langfuse: true\n  host: https://a.example.com\n")
    set_config_value(project, "telemetry.langfuse", "false")
    set_config_value(project, "telemetry.host", "")
    text = read(project)
    telemetry = load_config(project).telemetry
    assert telemetry is not None and telemetry.langfuse is False and telemetry.host == ""
    assert len(entries(text, "langfuse")) == 1
    assert "a.example.com" not in text


# @ac AC-PROJ-032.3
@pytest.mark.parametrize(
    "key, value, said",
    [("telemetry.langfuse", "maybe", ("true", "false")), ("telemetry.host", "langfuse.example.com", ("http://", "https://"))],
    ids=["langfuse", "host"],
)
def test_ac_proj_032_3_values_refused(project, key, value, said):
    before = read(project)
    with pytest.raises(ConfigError) as error:
        set_config_value(project, key, value)
    assert all(word in str(error.value) for word in said)
    assert read(project) == before


# @ac AC-PROJ-025.8
def test_ac_proj_025_8_an_unknown_telemetry_key_is_refused(project):
    before = read(project)
    with pytest.raises(ConfigError) as error:
        set_config_value(project, "telemetry.secret_key", "sk-test")
    assert "unknown config key" in str(error.value)
    assert "telemetry.langfuse" in str(error.value) and "telemetry.host" in str(error.value)
    assert read(project) == before


# --- the event log (REQ-PROJ-030) --------------------------------------------


# @ac AC-PROJ-030.1
def test_ac_proj_030_1_an_event_recorded(project):
    opt_in(project)
    change = add_change(project, "specify")
    record_event(change, enabled(project), "gate", passed=False)
    last = event_lines(change.path)[-1]
    assert last["event"] == "gate" and last["phase"] == "specify" and last["passed"] is False
    assert isinstance(last["at"], str) and last["at"]
    assert (change.path / "events.jsonl").read_text(encoding="utf-8").endswith("\n")


# @ac AC-PROJ-030.2
def test_ac_proj_030_2_kept_out_of_git(project):
    change = add_change(project)
    opt_in(project)
    assert not (change.path / ".gitignore").exists()
    record_event(change, enabled(project), "gate", passed=True)
    ignore = (change.path / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "events.jsonl" in ignore and "events.sent" in ignore
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=project, capture_output=True, text=True, check=True).stdout
    assert "events.jsonl" not in status


# @ac AC-PROJ-030.3
@pytest.mark.parametrize("block", ["", "telemetry:\n  langfuse: false\n"], ids=["no block", "false"])
def test_ac_proj_030_3_telemetry_off(project, block):
    write(project, read(project) + block)
    change = add_change(project)
    record_event(change, enabled(project), "gate", passed=True)
    assert not (change.path / "events.jsonl").exists()
    assert not (change.path / ".gitignore").exists()


# @ac AC-PROJ-030.4
def test_ac_proj_030_4_a_log_that_cannot_be_written(project):
    change = add_change(project)
    opt_in(project)
    (change.path / "events.jsonl").mkdir()
    (change.path / "events.jsonl" / "keep").write_text("x", encoding="utf-8")
    record_event(change, enabled(project), "gate", passed=True)
    folder = change.path / "events.jsonl"
    assert folder.is_dir() and [p.name for p in folder.iterdir()] == ["keep"]
    assert (folder / "keep").read_text(encoding="utf-8") == "x"


# @ac AC-PROJ-030.5
@pytest.mark.parametrize("abandoned", ["", "not needed"], ids=["closed", "abandoned"])
def test_ac_proj_030_5_the_log_moves_with_the_change(project, abandoned):
    change = add_change(project)
    opt_in(project)
    record_event(change, enabled(project), "gate", passed=False)
    record_event(change, enabled(project), "commit", sha="abc1234")
    log = (change.path / "events.jsonl").read_bytes()
    ignore = (change.path / ".gitignore").read_bytes()
    target = archive_change(change, load_config(project).archive_path, abandoned=abandoned)
    assert (target / "events.jsonl").read_bytes() == log
    assert (target / ".gitignore").read_bytes() == ignore
    assert [json.loads(line)["event"] for line in log.decode("utf-8").splitlines()] == ["gate", "commit"]


# @ac AC-PROJ-030.6
def test_ac_proj_030_6_an_existing_gitignore(project):
    change = add_change(project)
    opt_in(project)
    (change.path / ".gitignore").write_text("chat.jsonl\n", encoding="utf-8")
    record_event(change, enabled(project), "gate", passed=True)
    names = (change.path / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert sorted(names) == ["chat.jsonl", "events.jsonl", "events.sent"]
    record_event(change, enabled(project), "commit", sha="abc1234")
    assert (change.path / ".gitignore").read_text(encoding="utf-8").splitlines() == names


# --- the trace identity (REQ-PROJ-031) ---------------------------------------


# @ac AC-PROJ-031.1
def test_ac_proj_031_1_stable(project):
    change = add_change(project)
    first, second = trace_id("(top)", change), trace_id("(top)", load_change(load_config(project), REF))
    archive_change(change, load_config(project).archive_path)
    archived = archived_as(load_config(project), REF)
    assert archived is not None
    assert first == second == trace_id("(top)", archived)
    assert re.fullmatch(r"[0-9a-f]{32}", first)
    assert session_id(REF) == "add-login"


# @ac AC-PROJ-031.2
def test_ac_proj_031_2_distinct_per_change(tmp_path):
    created = "2026-11-03T10:00:00"
    top = Change(name="cleanup", path=tmp_path / "top/cleanup", created=created)
    billing = Change(name="cleanup", path=tmp_path / "billing/cleanup", created=created)
    assert trace_id("(top)", top) != trace_id("billing", billing)
    assert session_id("cleanup") == "cleanup"
    assert session_id("billing:cleanup") == "billing:cleanup"
