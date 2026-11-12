"""
Helpers shared by the modules tests of several capabilities.
"""

import json

from typer.testing import CliRunner

from helpers import init_repo
from specworks.cli import app

runner = CliRunner()


def run(*args):
    result = runner.invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return result.output


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    return result.exit_code, json.loads(result.output)


def make_workspace(tmp_path, monkeypatch):
    """
    Top-level project with module billing (services/billing) and nested module billing/tax.
    """
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    run("init")
    (tmp_path / ".specworks/config.yml").write_text(
        (tmp_path / ".specworks/config.yml").read_text().replace("context: |\n", "context: |\n  Company-wide: Python 3.12\n")
    )
    run("module", "add", "services/billing")
    billing = tmp_path / "services/billing"
    (billing / ".specworks/config.yml").write_text(
        (billing / ".specworks/config.yml").read_text()
        .replace("context: |\n", "context: |\n  Billing: money is Decimal\n")
        .replace("capabilities: {}", "capabilities:\n  invoices:\n    path: src/invoices")
    )
    monkeypatch.chdir(billing)
    run("module", "add", "tax")
    monkeypatch.chdir(tmp_path)
    return tmp_path
