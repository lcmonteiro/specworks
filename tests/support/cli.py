"""Helpers shared by the cli tests of several capabilities."""

import json

from typer.testing import CliRunner

from helpers import init_repo
from specworks.cli import app
from specworks.cli import project as project_cli

runner = CliRunner()


def make_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.output
    return tmp_path


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    return result.exit_code, json.loads(result.output)


def make_new_project(tmp_path, monkeypatch):
    """An empty folder in a git repository, before init."""
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    return tmp_path


def in_a_terminal(monkeypatch, answer=True):
    monkeypatch.setattr(project_cli, "is_terminal", lambda: answer)
