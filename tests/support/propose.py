"""
Helpers shared by the propose tests of several capabilities.
"""

import json

import pytest
from typer.testing import CliRunner

from helpers import init_repo
from samples import DELTA, LIVING, PROPOSAL, TASKS
from specworks.cli import app

runner = CliRunner()


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        pytest.fail(result.output)


def make_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    cfg = tmp_path / ".specworks/config.yml"
    cfg.write_text(
        cfg.read_text().replace(
            "capabilities: {}", "capabilities:\n  user-auth:\n    path: src/auth\n    prefix: AUTH\n  billing:\n    path: src/billing"
        )
    )
    (tmp_path / "src/auth/docs").mkdir(parents=True)
    (tmp_path / "src/auth/docs/spec.md").write_text(LIVING)
    run_json("new", "add-password-reset", "--no-branch")
    return tmp_path


def make_change(project):
    path = project / ".specworks/changes/active/add-password-reset"
    (path / "proposal.md").write_text(PROPOSAL)
    (path / "specs/user-auth").mkdir(parents=True)
    (path / "specs/user-auth/spec.md").write_text(DELTA)
    (path / "tasks.md").write_text(TASKS)
    return path


def errors(data):
    return [i["message"] for i in data["issues"] if i["level"] == "error"]
