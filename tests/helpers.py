"""Shared helpers for tests that need a planned change (proposal, delta spec and tasks)."""

import json

import pytest
from typer.testing import CliRunner

from specworks.cli import app

from test_propose import DELTA, LIVING, PROPOSAL, TASKS

runner = CliRunner()
REF = "add-password-reset"


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        pytest.fail(result.output)


def make_planned_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["init", "--dir", "spec", "--no-skills"]).exit_code == 0
    cfg = tmp_path / "spec.yml"
    cfg.write_text(cfg.read_text().replace("capabilities: {}", "capabilities:\n  user-auth:\n    path: src/auth\n    prefix: AUTH"))
    (tmp_path / "src/auth/docs").mkdir(parents=True)
    (tmp_path / "src/auth/docs/spec.md").write_text(LIVING)
    run_json("new", REF)
    change = tmp_path / "spec/changes" / REF
    (change / "proposal.md").write_text(PROPOSAL)
    (change / "specs/user-auth").mkdir(parents=True)
    (change / "specs/user-auth/spec.md").write_text(DELTA)
    (change / "tasks.md").write_text(TASKS)
    return tmp_path


def write_tests(root, *acs):
    (root / "tests").mkdir(exist_ok=True)
    body = "".join(f"# @ac {ac}\ndef test_{ac.lower().replace('-', '_').replace('.', '_')}():\n    assert False\n\n" for ac in acs)
    (root / "tests/test_reset.py").write_text(body)
