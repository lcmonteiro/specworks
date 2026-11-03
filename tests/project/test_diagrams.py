from helpers import init_repo
from specworks.cli import app
from support.diagrams import run_json, runner


# @ac AC-PROJ-009.3
def test_init_sets_the_diagram_theme(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-skills", "--diagram-theme", "Cool Classics"]).exit_code == 0
    assert "  theme: cool-classics\n" in (tmp_path / ".specworks/config.yml").read_text()
    code, data = run_json("diagrams", "--themes")
    assert data["theme"] == "cool-classics"


# @ac AC-PROJ-009.3
def test_init_rejects_unknown_diagram_theme(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["init", "--no-skills", "--diagram-theme", "rainbow"])
    assert result.exit_code == 1 and "unknown theme" in result.output
    assert not list(tmp_path.glob("*.yml")) and not (tmp_path / ".specworks/config.yml").exists()
