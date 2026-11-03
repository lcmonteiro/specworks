import json

from helpers import set_saved_tools
from specworks.cli import app
from specworks.core.config import load_config
from support.skills import SKILL, init, installed_files, runner, specworks_skills_in, state_of


# @ac AC-CLI-009.1
def test_update_refreshes_outdated_skills(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    edited, deleted = (f".claude/skills/{n}/SKILL.md" for n in (SKILL, "specworks-build"))
    (tmp_path / edited).write_text("edited\n", encoding="utf-8")
    (tmp_path / deleted).unlink()
    (tmp_path / ".claude/skills/specworks-propose").mkdir()
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert f"updated {edited}" in result.output and f"updated {deleted}" in result.output
    assert "removed .claude/skills/specworks-propose" in result.output
    assert state_of(tmp_path) == ("current", set())


# @ac AC-CLI-009.2
def test_update_on_current_skills_writes_nothing(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "all")
    before = {p: p.stat().st_mtime_ns for p in installed_files(tmp_path)}
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert "skills up to date" in result.output and "updated" not in result.output
    assert {p: p.stat().st_mtime_ns for p in installed_files(tmp_path)} == before


# @ac AC-CLI-009.3
def test_update_keeps_the_installed_tools(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    set_saved_tools(tmp_path, None)  # a project from before tools were saved
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github/copilot-instructions.md").write_text("# Copilot\n")
    (tmp_path / f".claude/skills/{SKILL}/SKILL.md").write_text("edited\n", encoding="utf-8")
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert f"updated .claude/skills/{SKILL}/SKILL.md" in result.output
    assert not (tmp_path / ".github/skills").exists() and not (tmp_path / ".github/prompts").exists()
    assert load_config(tmp_path).tools == ["claude"]
    assert "tools: [claude]" in (tmp_path / ".specworks/config.yml").read_text(encoding="utf-8")


# @ac AC-CLI-009.5
def test_update_with_both_tools_in_one_folder_is_up_to_date(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude,copilot")
    set_saved_tools(tmp_path, "[claude, copilot]")
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert "skills up to date" in result.output and "updated" not in result.output
    assert specworks_skills_in(tmp_path / ".github/skills") == []


# @ac AC-CLI-009.4
def test_update_from_a_module_updates_the_workspace_root(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    result = runner.invoke(app, ["init", "service", "--no-skills"])
    assert result.exit_code == 0, result.output
    (tmp_path / f".claude/skills/{SKILL}/SKILL.md").write_text("edited\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path / "service")
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert f"updated .claude/skills/{SKILL}/SKILL.md" in result.output
    assert not (tmp_path / "service/.claude").exists()
    assert state_of(tmp_path) == ("current", set())


# @ac AC-CLI-004.5
def test_context_shows_the_skills_state(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    data = json.loads(runner.invoke(app, ["context", "--json"]).output)
    assert data["skills"] == {"state": "current", "files": []}
    assert "run specworks update" not in runner.invoke(app, ["context"]).output
    (tmp_path / f".claude/skills/{SKILL}/SKILL.md").write_text("edited\n", encoding="utf-8")
    data = json.loads(runner.invoke(app, ["context", "--json"]).output)
    assert data["skills"] == {"state": "outdated", "files": [{"path": f".claude/skills/{SKILL}/SKILL.md", "reason": "changed"}]}
    assert "skills out of date: run specworks update" in runner.invoke(app, ["context"]).output
