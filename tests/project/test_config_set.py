import pytest

from specworks.core.config import MAX_CONTEXT_BYTES, load_config
from specworks.core.config_file import DEFAULT_CONFIG, set_config_value
from specworks.core.errors import ConfigError
from support.config_set import CONFIG, entries, make_project, read


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


def write(root, text):
    (root / CONFIG).write_text(text, encoding="utf-8")


def with_commands(root, test, lint):
    """The default config with `test` and `lint` set, as text."""
    write(root, read(root).replace("commands:\n  test:\n  lint:\n", f"commands:\n  test: {test}\n  lint: {lint}\n"))


def comments(text):
    return [line for line in text.splitlines() if line.lstrip().startswith("#")]


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


# @ac AC-PROJ-025.13
def test_ac_proj_025_13_the_scoped_test_command(project):
    set_config_value(project, "commands.test_scoped", "uv run pytest {paths}")
    text = read(project)
    assert load_config(project).commands["test_scoped"] == "uv run pytest {paths}"
    assert len(entries(text, "test_scoped")) == 1
    with pytest.raises(ConfigError) as error:
        set_config_value(project, "commands.test_scoped", "uv run pytest")
    assert "{paths}" in str(error.value)
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
