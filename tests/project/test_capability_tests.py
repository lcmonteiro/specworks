"""A capability's test folder, the scoped test command, and the review gate running only the touched capabilities' tests."""

import os
import re
import shlex
import subprocess

import pytest

from helpers import on_a_branch, run_json
from specworks.core.runner import run_scoped, scoped_command
from specworks.core.workspace import load_workspace
from support.capability_tests import add_billing_module, commands_block, make_log, new_project, runs, write


def quoted(path):
    """A folder quoted for the platform's shell, as the scoped command fills it in."""
    return subprocess.list2cmdline([path]) if os.name == "nt" else shlex.quote(path)


@pytest.fixture
def log(tmp_path_factory):
    return make_log(tmp_path_factory)


# --- a capability's test folder -------------------------------------------------


def folder_of(root, name):
    ws = load_workspace(root)
    (mod, cap), *_ = [(m, c) for m, c in ws.capabilities() if m.qualify(c.name) == name]
    return cap.tests_path(mod.root, mod.config.tests_dir)


# @ac AC-PROJ-027.1
def test_ac_proj_027_1_the_default_test_folder(tmp_path, monkeypatch):
    new_project(tmp_path, monkeypatch, capabilities="  auth:\n    path: src/auth\n")
    assert folder_of(tmp_path, "auth") == tmp_path / "tests/auth"
    assert not (tmp_path / "tests/auth").exists()  # known whether or not it exists


# @ac AC-PROJ-027.2
def test_ac_proj_027_2_the_modules_tests_dir(tmp_path, monkeypatch):
    new_project(tmp_path, monkeypatch, capabilities="  auth:\n    path: src/auth\n", config_tail="tests_dir: test\n")
    assert folder_of(tmp_path, "auth") == tmp_path / "test/auth"


# @ac AC-PROJ-027.3
@pytest.mark.parametrize("tests_dir", ["", "tests_dir: spec\n"], ids=["default", "spec"])
def test_ac_proj_027_3_a_capabilitys_own_tests_folder(tmp_path, monkeypatch, tests_dir):
    new_project(tmp_path, monkeypatch, capabilities="  auth:\n    path: src/auth\n    tests: src/auth\n", config_tail=tests_dir)
    assert folder_of(tmp_path, "auth") == tmp_path / "src/auth"


# @ac AC-PROJ-027.4
def test_ac_proj_027_4_inside_a_module(tmp_path, monkeypatch):
    new_project(tmp_path, monkeypatch, capabilities="  auth:\n    path: src/auth\n", config_tail="tests_dir: tests\n")
    add_billing_module(tmp_path, "tests_dir: spec\n")
    assert folder_of(tmp_path, "billing:invoices") == tmp_path / "services/billing/spec/invoices"
    assert folder_of(tmp_path, "auth") == tmp_path / "tests/auth"


# --- config checks ----------------------------------------------------------------


# @ac AC-PROJ-003.1
@pytest.mark.parametrize(
    "tests", ["../outside", "/etc", "src/../../outside"], ids=["up", "absolute", "inner-up"],
)
def test_ac_proj_003_1_a_capabilitys_tests_stays_inside_the_project(tmp_path, monkeypatch, tests):
    new_project(tmp_path, monkeypatch, capabilities=f"  auth:\n    path: src/auth\n    tests: {tests}\n")
    code, data = run_json("context")
    assert code == 1 and "must be a relative folder inside the project" in data["error"], data
    assert "auth" in data["error"] and "tests" in data["error"], data  # names the setting


# @ac AC-PROJ-003.1
@pytest.mark.parametrize("capabilities, tail", [("", "tests_dir: 3\n"), ("  auth:\n    path: src/auth\n    tests: ''\n", "")], ids=["tests_dir", "tests"])
def test_ac_proj_003_1_a_test_folder_must_be_a_non_empty_string(tmp_path, monkeypatch, capabilities, tail):
    new_project(tmp_path, monkeypatch, capabilities=capabilities, config_tail=tail)
    code, data = run_json("context")
    assert code == 1 and "tests" in data["error"], data


# @ac AC-PROJ-003.8
def test_ac_proj_003_8_a_scoped_test_command_without_its_placeholder(tmp_path, monkeypatch):
    new_project(tmp_path, monkeypatch, commands="commands:\n  test: uv run pytest\n  test_scoped: uv run pytest\n")
    code, data = run_json("context")
    assert code == 1 and "commands.test_scoped" in data["error"] and "{paths}" in data["error"], data
    cfg = tmp_path / ".specworks/config.yml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("  test_scoped: uv run pytest\n", "  test_scoped: uv run pytest {paths}\n"), encoding="utf-8")
    code, data = run_json("context")
    assert code == 0 and data["commands"]["test_scoped"] == "uv run pytest {paths}", data


# --- running the scoped tests -----------------------------------------------------


# @ac AC-PROJ-028.1
def test_ac_proj_028_1_the_folders_filled_in(tmp_path, monkeypatch):
    new_project(tmp_path, monkeypatch, commands="commands:\n  test: uv run pytest\n  test_scoped: uv run pytest {paths}\n")
    ws = load_workspace(tmp_path)
    command = scoped_command(ws, ws.top, [tmp_path / "tests/auth", tmp_path / "tests/my tests"])
    assert command == f"uv run pytest tests/auth {quoted('tests/my tests')}"


# @ac AC-PROJ-028.1
def test_ac_proj_028_1_a_test_folder_that_links_outside_the_module_keeps_its_own_path(tmp_path, monkeypatch, tmp_path_factory):
    new_project(tmp_path, monkeypatch, commands="commands:\n  test: uv run pytest\n  test_scoped: uv run pytest {paths}\n")
    shared = tmp_path_factory.mktemp("shared") / "auth"
    shared.mkdir()
    (tmp_path / "tests").mkdir(exist_ok=True)
    try:
        (tmp_path / "tests/auth").symlink_to(shared, target_is_directory=True)
    except OSError:  # Windows without the symlink privilege
        pytest.skip("cannot create symlinks here")
    ws = load_workspace(tmp_path)
    assert scoped_command(ws, ws.top, [tmp_path / "tests/auth"]) == "uv run pytest tests/auth"


# @ac AC-PROJ-028.1
def test_ac_proj_028_1_the_scoped_run_reports_its_exit_code_and_output(tmp_path, monkeypatch, log):
    new_project(tmp_path, monkeypatch, commands=commands_block(log))
    write(tmp_path / "tests/my tests/test_x.py", "def test_x():\n    assert False\n")
    ws = load_workspace(tmp_path)
    result = run_scoped(ws, ws.top, [tmp_path / "tests/auth", tmp_path / "tests/my tests"], reuse=False)
    assert runs(log, tmp_path) == [("scoped", ["tests/auth", "tests/my tests"], ".")]
    assert result.exit_code == 1 and not result.ok and result.cwd == "." and "scoped 2 failed" in result.output


# @ac AC-PROJ-028.2
def test_ac_proj_028_2_in_a_module(tmp_path, monkeypatch, log):
    new_project(tmp_path, monkeypatch, commands="commands:\n  test: uv run pytest\n")
    billing = add_billing_module(tmp_path, "tests_dir: spec\n")
    cfg = billing / ".specworks/config.yml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("commands:\n  test:\n  lint:\n", commands_block(log)), encoding="utf-8")
    ws = load_workspace(tmp_path)
    module = ws.module("billing")
    result = run_scoped(ws, module, [billing / "spec/invoices"], reuse=False)
    assert runs(log, tmp_path) == [("scoped", ["spec/invoices"], "services/billing")]
    assert result.ok and result.cwd == "services/billing", result


# @ac AC-PROJ-028.3
def test_ac_proj_028_3_reused_only_for_the_same_folders(tmp_path, monkeypatch, log):
    new_project(tmp_path, monkeypatch, commands=commands_block(log))
    on_a_branch(tmp_path, monkeypatch)
    ws = load_workspace(tmp_path)
    auth, billing = tmp_path / "tests/auth", tmp_path / "tests/billing"
    run_scoped(ws, ws.top, [auth])
    second = run_scoped(ws, ws.top, [auth, billing])
    assert len(runs(log, tmp_path)) == 2 and second.cached_at == ""  # other folders: a real run
    third = run_scoped(ws, ws.top, [auth, billing])
    assert len(runs(log, tmp_path)) == 2 and third.cached_at != "" and third.ok  # the same folders: reused


# --- specworks run test_scoped ----------------------------------------------------


# @ac AC-PROJ-013.5
def test_ac_proj_013_5_the_scoped_test_command_run_directly_is_refused(tmp_path, monkeypatch, log):
    new_project(tmp_path, monkeypatch, commands=commands_block(log))
    code, data = run_json("run", "test_scoped")
    assert code == 1 and "{paths}" in data["error"] and "review gate" in data["error"], data
    assert re.search(r"\btest\b", data["error"]), data  # points to `test` for the whole suite
    assert runs(log, tmp_path) == []  # nothing ran
