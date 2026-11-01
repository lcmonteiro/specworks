import json

import pytest
from typer.testing import CliRunner

from helpers import init_repo
from specworks.cli import app
from specworks.core.config import MAX_CONTEXT_BYTES, load_config
from specworks.core.config_file import DEFAULT_CONFIG, set_config_value
from specworks.core.errors import ConfigError

runner = CliRunner()
CONFIG = ".specworks/config.yml"


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A project with the default config written by `init`."""
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["init", "--no-skills"])
    assert result.exit_code == 0, result.output
    return tmp_path


def read(root):
    return (root / CONFIG).read_text(encoding="utf-8")


def write(root, text):
    (root / CONFIG).write_text(text, encoding="utf-8")


def with_commands(root, test, lint):
    """The default config with `test` and `lint` set, as text."""
    write(root, read(root).replace("commands:\n  test:\n  lint:\n", f"commands:\n  test: {test}\n  lint: {lint}\n"))


def entries(text, key):
    """The uncommented lines of ``text`` that hold ``key:`` (at any indent)."""
    return [line for line in text.splitlines() if line.strip().startswith(f"{key}:")]


def comments(text):
    return [line for line in text.splitlines() if line.lstrip().startswith("#")]


def invoke(*args, stdin=None):
    return runner.invoke(app, list(args), input=stdin)


def invoke_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        pytest.fail(result.output)


# --- set_config_value -------------------------------------------------------


# @ac AC-PROJ-025.1
def test_ac_proj_025_1_a_command_set_keeps_the_comments(project):
    before = read(project)
    set_config_value(project, "commands.test", "uv run pytest")
    text = read(project)
    assert load_config(project).commands["test"] == "uv run pytest"
    assert comments(before) and all(line in text.splitlines() for line in comments(before))
    assert len(entries(text, "test")) == 1


# @ac AC-PROJ-025.2
def test_ac_proj_025_2_a_command_replaced(project):
    with_commands(project, "pytest", "ruff check .")
    set_config_value(project, "commands.lint", "uv run ruff check src")
    text = read(project)
    assert load_config(project).commands == {"test": "pytest", "lint": "uv run ruff check src"}
    assert len(entries(text, "lint")) == 1


# @ac AC-PROJ-025.3
def test_ac_proj_025_3_a_command_added_to_a_config_without_commands(tmp_path):
    (tmp_path / ".specworks").mkdir()
    write(tmp_path, "specworks: 1\ncontext: |\n  A small service\ndocs_dir: docs\n")
    set_config_value(tmp_path, "commands.build", "make")
    config = load_config(tmp_path)
    assert config.commands == {"build": "make"}
    assert config.context == "A small service\n" and config.docs_dir == "docs"


# @ac AC-PROJ-025.4
@pytest.mark.parametrize("command", ['pytest -k "a or b" # all: yes', "'quoted' first", "make: all"])
def test_ac_proj_025_4_a_command_with_yaml_characters(project, command):
    set_config_value(project, "commands.test", command)
    assert load_config(project).commands["test"] == command
    assert len(entries(read(project), "test")) == 1


# @ac AC-PROJ-025.5
def test_ac_proj_025_5_a_command_cleared(project):
    with_commands(project, "pytest", "ruff check .")
    set_config_value(project, "commands.lint", "")
    assert load_config(project).commands == {"test": "pytest"}


# @ac AC-PROJ-025.6
def test_ac_proj_025_6_the_context_set(project):
    before_text, before = read(project), load_config(project)
    context = "Python 3.11+ CLI (typer).\nTests in tests/ (pytest).\nDocs in the wiki.\n"
    set_config_value(project, "context", context)
    after = load_config(project)
    assert after.context == context
    tail = "# Name of the folder"  # the first entry after `context:` in the default config
    assert read(project).split(tail, 1)[1] == before_text.split(tail, 1)[1]
    assert (after.docs_dir, after.capabilities, after.modules, after.commands, after.diagrams, after.test_globs, after.source_globs) == (
        before.docs_dir, before.capabilities, before.modules, before.commands, before.diagrams, before.test_globs, before.source_globs,
    )


# @ac AC-PROJ-025.7
def test_ac_proj_025_7_the_context_replaced(project):
    write(project, read(project).replace("context: |\n", "context: |\n  Old line one\n  Old line two\n"))
    assert load_config(project).context == "Old line one\nOld line two\n"
    set_config_value(project, "context", "New text\n")
    text = read(project)
    assert load_config(project).context == "New text\n"
    assert "Old line" not in text
    assert len([line for line in text.splitlines() if line.startswith("context:")]) == 1


# @ac AC-PROJ-025.8
@pytest.mark.parametrize("key", ["commands.unit", "docs_dir"])
def test_ac_proj_025_8_an_unknown_key_is_refused(project, key):
    before = read(project)
    with pytest.raises(ConfigError) as error:
        set_config_value(project, key, "pytest")
    assert "unknown config key" in str(error.value)
    assert "use one of: context, commands.test" in str(error.value)
    assert read(project) == before


# @ac AC-PROJ-025.9
def test_ac_proj_025_9_an_entry_the_text_edit_cannot_change(tmp_path):
    (tmp_path / ".specworks").mkdir()
    write(tmp_path, "specworks: 1\ncommands: {test: pytest}\n")
    before = read(tmp_path)
    with pytest.raises(ConfigError) as error:
        set_config_value(tmp_path, "commands.lint", "ruff check .")
    assert "set it by hand" in str(error.value) and "commands.lint" in str(error.value)
    assert read(tmp_path) == before


# @ac AC-PROJ-025.9
def test_ac_proj_025_9_an_edit_that_does_not_load_is_restored(tmp_path):
    # A 4-space `commands:` block gets a 2-space line, which does not load: the file is restored.
    (tmp_path / ".specworks").mkdir()
    write(tmp_path, "specworks: 1\n# the commands\ncommands:\n    test: pytest\n")
    before = read(tmp_path)
    with pytest.raises(ConfigError) as error:
        set_config_value(tmp_path, "commands.lint", "ruff check .")
    assert "set it by hand" in str(error.value) and "commands.lint" in str(error.value)
    assert read(tmp_path) == before


# @ac AC-PROJ-025.6
def test_ac_proj_025_6_the_context_added_to_a_config_without_one(tmp_path):
    (tmp_path / ".specworks").mkdir()
    write(tmp_path, "specworks: 1\n# the docs folder\ndocs_dir: docs\ncommands:\n  test: pytest\n")
    context = "Line one\nLine two\nLine three\n"
    set_config_value(tmp_path, "context", context)
    text = read(tmp_path)
    config = load_config(tmp_path)
    assert config.context == context
    assert (config.docs_dir, config.commands) == ("docs", {"test": "pytest"})
    assert "# the docs folder" in text
    assert len([line for line in text.splitlines() if line.startswith("context:")]) == 1


# @ac AC-PROJ-025.10
def test_ac_proj_025_10_a_command_added_to_the_commands_block(project):
    with_commands(project, "pytest", "ruff check .")
    before = read(project)
    set_config_value(project, "commands.typecheck", "uv run mypy")
    text = read(project)
    assert load_config(project).commands == {"test": "pytest", "lint": "ruff check .", "typecheck": "uv run mypy"}
    assert len(entries(text, "typecheck")) == 1
    assert len([line for line in text.splitlines() if line.startswith("commands:")]) == 1
    assert comments(before) and all(line in text.splitlines() for line in comments(before))


# @ac AC-PROJ-025.10
def test_ac_proj_025_10_a_command_added_to_the_default_commands_block(project):
    before = read(project)
    set_config_value(project, "commands.typecheck", "uv run mypy")
    text = read(project)
    assert load_config(project).commands == {"typecheck": "uv run mypy"}  # test and lint stay empty, as init wrote them
    assert len(entries(text, "test")) == 1 and len(entries(text, "lint")) == 1
    assert len(entries(text, "typecheck")) == 1
    assert len([line for line in text.splitlines() if line.startswith("commands:")]) == 1
    assert all(line in text.splitlines() for line in comments(before))


# @ac AC-PROJ-025.11
def test_ac_proj_025_11_a_context_over_the_size_limit_is_refused(project):
    before = read(project)
    with pytest.raises(ConfigError) as error:
        set_config_value(project, "context", "x" * (MAX_CONTEXT_BYTES + 1))
    assert str(MAX_CONTEXT_BYTES) in str(error.value)
    assert read(project) == before


# @ac AC-PROJ-025.12
def test_ac_proj_025_12_the_branch_setting(project):
    set_config_value(project, "branch_per_change", "false")
    text = read(project)
    assert load_config(project).branch_per_change is False
    assert len(entries(text, "branch_per_change")) == 1
    with pytest.raises(ConfigError) as error:
        set_config_value(project, "branch_per_change", "maybe")
    assert "branch_per_change must be true or false" in str(error.value)
    assert read(project) == text


# --- branch_per_change ------------------------------------------------------


# @ac AC-PROJ-026.1
def test_ac_proj_026_1_the_default_is_true_and_the_default_config_names_it(project, tmp_path_factory):
    bare = tmp_path_factory.mktemp("bare")
    (bare / ".specworks").mkdir()
    write(bare, "specworks: 1\n")
    assert load_config(bare).branch_per_change is True
    assert load_config(project).branch_per_change is True
    assert "branch_per_change" in read(project)
    assert "# branch_per_change: false" in DEFAULT_CONFIG
    assert entries(read(project), "branch_per_change") == []  # described, not set


# @ac AC-PROJ-026.2
def test_ac_proj_026_2_set_to_false(tmp_path):
    (tmp_path / ".specworks").mkdir()
    write(tmp_path, "specworks: 1\nbranch_per_change: false\n")
    assert load_config(tmp_path).branch_per_change is False


# @ac AC-PROJ-026.3
def test_ac_proj_026_3_a_value_that_is_not_true_or_false_is_refused(tmp_path):
    (tmp_path / ".specworks").mkdir()
    write(tmp_path, "specworks: 1\nbranch_per_change: sometimes\n")
    with pytest.raises(ConfigError) as error:
        load_config(tmp_path)
    assert "'branch_per_change' must be true or false" in str(error.value)


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


# @ac AC-CLI-013.2
def test_ac_cli_013_2_an_unreadable_file_is_refused(project):
    before = read(project)
    code, data = invoke_json("config", "set", "context", "--file", "missing.txt")
    assert code == 1 and "cannot read missing.txt" in data["error"], data
    assert read(project) == before
