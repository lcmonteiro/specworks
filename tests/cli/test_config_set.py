import json

import pytest

from specworks.cli import app
from specworks.core.config import load_config
from support.config_set import CONFIG, entries, invoke, make_project, read, runner


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


def invoke_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        pytest.fail(result.output)


# --- specworks config set ---------------------------------------------------


# @ac AC-CLI-013.1
def test_ac_cli_013_1_setting_a_command(project):
    code, data = invoke_json("config", "set", "commands.test", "uv run pytest")
    assert code == 0, data
    assert data["key"] == "commands.test" and data["value"] == "uv run pytest"
    assert data["config"] == CONFIG
    code, context = invoke_json("context")
    assert code == 0 and context["commands"]["test"] == "uv run pytest"


# @ac AC-CLI-013.2
@pytest.mark.parametrize("source", ["file", "stdin"])
def test_ac_cli_013_2_the_context_from_a_file_or_standard_input(project, source):
    context = "First line\nSecond line\n"
    if source == "file":
        (project / "notes.txt").write_text(context, encoding="utf-8")
        result = invoke("config", "set", "context", "--file", "notes.txt")
    else:
        result = invoke("config", "set", "context", "--file", "-", stdin=context)
    assert result.exit_code == 0, result.output
    assert load_config(project).context == context


# @ac AC-CLI-013.3
@pytest.mark.parametrize(
    "args, message",
    [(["text", "--file", "notes.txt"], "not both"), ([], "- for standard input")],
    ids=["both", "neither"],
)
def test_ac_cli_013_3_both_a_value_and_a_file_or_neither_is_refused(project, args, message):
    (project / "notes.txt").write_text("from the file\n", encoding="utf-8")
    before = read(project)
    code, data = invoke_json("config", "set", "context", *args)
    assert code == 1 and message in data["error"], data
    assert read(project) == before


# @ac AC-CLI-013.4
def test_ac_cli_013_4_in_a_module(project):
    assert invoke("module", "add", "services/billing").exit_code == 0
    billing = project / "services/billing"
    top = read(project)
    result = invoke("config", "set", "commands.test", "go test ./...", "--module", "billing")
    assert result.exit_code == 0, result.output
    assert load_config(billing).commands["test"] == "go test ./..."
    assert read(project) == top


# @ac AC-CLI-013.5
def test_ac_cli_013_5_a_refused_key_under_json(project):
    before = read(project)
    code, data = invoke_json("config", "set", "commands.unit", "pytest")
    assert code == 1 and "error" in data, data
    assert "unknown config key" in data["error"]
    assert read(project) == before


# @ac AC-CLI-013.6
@pytest.mark.parametrize("where", ["inside", "option"])
def test_ac_cli_013_6_the_branch_setting_from_inside_a_module(project, monkeypatch, where):
    assert invoke("module", "add", "services/billing").exit_code == 0
    billing = project / "services/billing"
    billing_before = read(billing)
    if where == "inside":
        monkeypatch.chdir(billing)
        code, data = invoke_json("config", "set", "branch_per_change", "false")
    else:
        code, data = invoke_json("config", "set", "branch_per_change", "false", "--module", "billing")
    assert code == 0, data
    assert entries(read(project), "branch_per_change") == ["branch_per_change: false"]
    assert load_config(project).branch_per_change is False
    assert read(billing) == billing_before
    assert data["config"] == CONFIG


# @ac AC-CLI-013.2
def test_ac_cli_013_2_an_unreadable_file_is_refused(project):
    before = read(project)
    code, data = invoke_json("config", "set", "context", "--file", "missing.txt")
    assert code == 1 and "cannot read missing.txt" in data["error"], data
    assert read(project) == before
