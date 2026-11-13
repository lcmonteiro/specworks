"""
Code phase support: `specworks run` and the code gate.
"""

import json
import sys

from typer.testing import CliRunner

from helpers import REF, run_json
from specworks.cli import app
from support.code_phase import FAIL, PASS, set_test_command

runner = CliRunner()


# --- specworks run ----------------------------------------------------------


# @ac AC-PROJ-013.1
def test_run_passes_the_exit_code_through(project):
    set_test_command(project, FAIL)
    code, data = run_json("run", "test")
    assert code == 3 and data["ok"] is False and data["tail"] == ["2 failed"]
    set_test_command(project, PASS)
    code, data = run_json("run", "test", "--change", REF)
    assert code == 0 and data["ok"] is True and data["cwd"] == "."


# @ac AC-PROJ-013.2
def test_run_in_the_module_of_the_change(project):
    runner.invoke(app, ["module", "add", "web"])
    web_cfg = project / "web/.specworks/config.yml"
    pwd = f'"{sys.executable}" -c "import os; print(os.path.basename(os.getcwd()))"'
    web_cfg.write_text(web_cfg.read_text().replace("commands:\n  test:\n", f"commands:\n  test: {json.dumps(pwd)}\n"))
    run_json("new", "web-change", "--module", "web", "--no-branch")
    code, data = run_json("run", "test", "--change", "web:web-change")
    assert code == 0 and data["cwd"] == "web" and data["tail"] == ["web"]


# @ac AC-PROJ-013.3
def test_run_unconfigured_command(project):
    code, data = run_json("run", "lint")
    assert code == 1 and "no 'lint' command configured" in data["error"]
    assert "(e.g. lint: <command>)" in data["error"]


# @ac AC-PROJ-013.4
def test_run_unknown_command_key(project):
    code, data = run_json("run", "frobnicate")
    assert code == 1 and "unknown command 'frobnicate'" in data["error"]
    assert "test, test_scoped, lint, typecheck, build, format" in data["error"] and "commands:" not in data["error"]
