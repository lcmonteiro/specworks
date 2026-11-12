"""
Helpers shared by the config_set tests of several capabilities.
"""

from typer.testing import CliRunner

from helpers import init_repo
from specworks.cli import app

runner = CliRunner()
CONFIG = ".specworks/config.yml"


def make_project(tmp_path, monkeypatch):
    """
    A project with the default config written by `init`.
    """
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["init", "--no-skills"])
    assert result.exit_code == 0, result.output
    return tmp_path


def read(root):
    return (root / CONFIG).read_text(encoding="utf-8")


def entries(text, key):
    """
    The uncommented lines of ``text`` that hold ``key:`` (at any indent).
    """
    return [line for line in text.splitlines() if line.strip().startswith(f"{key}:")]


def invoke(*args, stdin=None):
    return runner.invoke(app, list(args), input=stdin)
