"""
The harness block in the project config: loaded and checked (REQ-PROJ-003), and its model set by text edit (REQ-PROJ-035, REQ-PROJ-025).
"""

import pytest

from specworks.core.config import HarnessConfig, load_config
from specworks.core.config_file import set_config_value
from specworks.core.errors import ConfigError
from support.config_set import CONFIG, entries, make_project, read
from support.modules import make_workspace, run_json


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


def write(root, text):
    (root / CONFIG).write_text(text, encoding="utf-8")


def comments(text):
    return [line for line in text.splitlines() if line.lstrip().startswith("#")]


def harness_model(root):
    harness = load_config(root).harness
    return (harness.model if harness is not None else "") or None


# --- the config block (REQ-PROJ-003) -----------------------------------------


# @ac AC-PROJ-003.11
@pytest.mark.parametrize(
    "block, named",
    [
        ("harness: o3\n", "harness"),
        ("harness:\n  model: o3\n  api_key: sk-test\n", "harness"),
        ("harness:\n  model: 3\n", "harness.model"),
        ("harness:\n  model: [o3]\n", "harness.model"),
        ('harness:\n  model: ""\n', "harness.model"),
        ("harness:\n  model:\n", "harness.model"),
    ],
    ids=["not a mapping", "another key", "a number", "a list", "empty", "null"],
)
def test_ac_proj_003_11_harness_refused(project, block, named):
    write(project, read(project) + block)
    with pytest.raises(ConfigError) as error:
        load_config(project)
    assert named in str(error.value)


# @ac AC-PROJ-003.11
def test_ac_proj_003_11_harness_loads(project):
    assert load_config(project).harness is None
    write(project, read(project) + "harness: {model: gpt-4.1}\n")
    assert load_config(project).harness == HarnessConfig(model="gpt-4.1")


# @ac AC-PROJ-003.12
def test_ac_proj_003_12_harness_in_a_module(tmp_path, monkeypatch):
    make_workspace(tmp_path, monkeypatch)
    billing = tmp_path / "services/billing" / CONFIG
    billing.write_text(billing.read_text(encoding="utf-8") + "harness:\n  model: o3\n", encoding="utf-8")
    code, data = run_json("context")
    assert code == 1, data
    assert "module 'billing': 'harness' is set in the top level's config, not in a module's; remove it" in data["error"]


# --- set_config_value (REQ-PROJ-035, REQ-PROJ-025) -----------------------------


# @ac AC-PROJ-035.1
def test_ac_proj_035_1_the_model_set_with_the_comments_kept(project):
    before = read(project)
    set_config_value(project, "harness.model", "gpt-4.1")
    text = read(project)
    assert harness_model(project) == "gpt-4.1"
    assert len(entries(text, "harness")) == 1 and len(entries(text, "model")) == 1
    assert comments(before) and all(line in text.splitlines() for line in comments(before))


# @ac AC-PROJ-035.2
def test_ac_proj_035_2_replaced_and_cleared(project):
    write(project, read(project) + "harness:\n  model: gpt-4.1\n")
    assert harness_model(project) == "gpt-4.1"
    set_config_value(project, "harness.model", "claude-sonnet-4")
    text = read(project)
    assert harness_model(project) == "claude-sonnet-4"
    assert len(entries(text, "model")) == 1 and "gpt-4.1" not in text
    set_config_value(project, "harness.model", "")
    text = read(project)
    assert harness_model(project) is None
    assert entries(text, "model") == []


# @ac AC-PROJ-035.3
def test_ac_proj_035_3_a_model_id_with_yaml_characters(project):
    set_config_value(project, "harness.model", "org/model: v2 # beta")
    assert harness_model(project) == "org/model: v2 # beta"


# @ac AC-PROJ-025.8
def test_ac_proj_025_8_an_unknown_harness_key_is_refused(project):
    before = read(project)
    with pytest.raises(ConfigError) as error:
        set_config_value(project, "harness.api_key", "sk-test")
    assert "unknown config key" in str(error.value)
    assert "harness.model" in str(error.value)
    assert read(project) == before
