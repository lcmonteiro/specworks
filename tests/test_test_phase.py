"""
Test phase support: commands config, task ticking and the specify/test gates.
"""

from typer.testing import CliRunner

from helpers import REF, run_json
from specworks.cli import app

runner = CliRunner()

# --- commands ---------------------------------------------------------------


def test_commands_are_inherited_and_overridden_by_modules(project, monkeypatch):
    cfg = project / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("commands:\n  test:\n  lint:\n", "commands:\n  test: uv run pytest\n  lint: ruff check .\n"))
    runner.invoke(app, ["module", "add", "web"])
    web = project / "web/.specworks/config.yml"
    web.write_text(web.read_text().replace("commands:\n  test:\n", "commands:\n  test: npm test\n"))
    code, data = run_json("context")
    assert data["commands"] == {"test": "uv run pytest", "lint": "ruff check ."}
    monkeypatch.chdir(project / "web")
    code, data = run_json("context")
    assert data["commands"] == {"test": "npm test", "lint": "ruff check ."}


def test_unknown_command_key_is_rejected(project):
    cfg = project / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("commands:\n  test:\n", "commands:\n  deploy: make\n  test:\n"))
    code, data = run_json("context")
    assert code == 1 and "unknown keys: deploy" in data["error"]


# --- tasks ------------------------------------------------------------------


def test_task_list(project):
    code, data = run_json("task", "list", "--change", REF)
    assert code == 0 and data["done"] == 1 and data["total"] == 3
    assert data["tasks"][0]["ids"] == ["AC-AUTH-003.1", "AC-AUTH-003.2"]
    code, data = run_json("task", "list", "--change", REF, "--pending")
    assert [t["num"] for t in data["tasks"]] == ["1.1", "1.2"]


def test_task_list_without_tasks_file(project):
    (project / ".specworks/changes/active" / REF / "tasks.md").unlink()
    code, data = run_json("task", "list", "--change", REF)
    assert code == 1 and "not written yet" in data["error"]
