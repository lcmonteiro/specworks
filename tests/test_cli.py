import json

import pytest
from typer.testing import CliRunner

from specworks.cli import app

runner = CliRunner()


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.output
    return tmp_path


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    return result.exit_code, json.loads(result.output)


def test_context_without_project_reports_null_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code, data = run_json("context")
    assert code == 1
    assert data["root"] is None


def test_init_creates_config_changes_and_skills(project):
    assert (project / "specworks.yaml").is_file()
    assert (project / "specworks/changes/archive").is_dir()
    assert (project / ".claude/skills/sw-refine/SKILL.md").is_file()


def test_new_change_starts_in_refine_phase(project):
    code, data = run_json("new", "add-login")
    assert code == 0
    assert data["phase"] == "refine"
    code, data = run_json("list")
    assert [c["name"] for c in data["changes"]] == ["add-login"]


@pytest.mark.parametrize("name", ["Add_Login", "add login", "x--y", "archive-"])
def test_new_rejects_non_kebab_names(project, name):
    code, data = run_json("new", name)
    assert code == 1
    assert "kebab-case" in data["error"]


def test_new_rejects_duplicates(project):
    run_json("new", "add-login")
    code, data = run_json("new", "add-login")
    assert code == 1 and "already exists" in data["error"]


def test_instructions_for_refinement(project):
    run_json("new", "add-login")
    code, data = run_json("instructions", "refinement", "--change", "add-login")
    assert code == 0
    assert data["outputPath"] == "specworks/changes/add-login/refinement.md"
    assert "## Options" in data["template"]
    assert data["exists"] is False


def test_status_marks_refinement_done_once_written(project):
    run_json("new", "add-login")
    (project / "specworks/changes/add-login/refinement.md").write_text("# Refinement\n")
    code, data = run_json("status", "--change", "add-login")
    states = {a["id"]: a["status"] for a in data["artifacts"]}
    assert states["refinement"] == "done"


def test_context_lists_capabilities_with_docs_path(project):
    (project / "specworks.yaml").write_text(
        "context: Python 3.12 service\ncapabilities:\n  user-auth:\n    path: src/auth\n"
    )
    code, data = run_json("context")
    assert code == 0
    assert data["context"] == "Python 3.12 service"
    assert data["capabilities"][0]["docsPath"] == "src/auth/docs"
    assert data["capabilities"][0]["hasSpec"] is False


def test_phase_moves_and_validates(project):
    run_json("new", "add-login")
    code, data = run_json("phase", "add-login", "propose")
    assert code == 0 and data["phase"] == "propose"
    code, data = run_json("phase", "add-login", "shipping")
    assert code == 1


@pytest.mark.parametrize("folder", ["spec", "docs", "context", "docs/spec"])
def test_init_with_custom_dir(tmp_path, monkeypatch, folder):
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["init", "--dir", folder]).exit_code == 0
    assert f"dir: {folder}\n" in (tmp_path / "specworks.yaml").read_text()
    assert (tmp_path / folder / "changes/archive").is_dir()
    assert not (tmp_path / "specworks").exists()
    code, data = run_json("new", "add-login")
    assert data["path"] == f"{folder}/changes/add-login"
    code, data = run_json("context")
    assert data["dir"] == folder and data["changesDir"] == f"{folder}/changes"


def test_dir_edited_in_config_is_used(project):
    text = (project / "specworks.yaml").read_text().replace("dir: specworks", "dir: context")
    (project / "specworks.yaml").write_text(text)
    code, data = run_json("new", "add-login")
    assert data["path"] == "context/changes/add-login"


@pytest.mark.parametrize("folder", ["/abs", "../outside", ".", ""])
def test_init_rejects_bad_dir(tmp_path, monkeypatch, folder):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--dir", folder])
    assert result.exit_code == 1
    assert not (tmp_path / "specworks.yaml").exists()


def test_bad_dir_in_config_is_reported(project):
    (project / "specworks.yaml").write_text("dir: ../elsewhere\n")
    code, data = run_json("context")
    assert code == 1 and "'dir'" in data["error"]
