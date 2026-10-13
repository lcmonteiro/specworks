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
    assert (project / "specworks.yml").is_file()
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
    (project / "specworks.yml").write_text(
        "specworks: 1\ncontext: Python 3.12 service\ncapabilities:\n  user-auth:\n    path: src/auth\n"
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


@pytest.mark.parametrize("folder", ["spec", "docs", "context", "specworks"])
def test_init_with_custom_dir_names_config_after_folder(tmp_path, monkeypatch, folder):
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["init", "--dir", folder]).exit_code == 0
    assert (tmp_path / f"{folder}.yml").read_text().startswith("specworks: 1\n")
    assert sorted(p.name for p in tmp_path.glob("*.yml")) == [f"{folder}.yml"]
    assert (tmp_path / folder / "changes/archive").is_dir()
    code, data = run_json("new", "add-login")
    assert data["path"] == f"{folder}/changes/add-login"
    code, data = run_json("context")
    assert data["dir"] == folder and data["changesDir"] == f"{folder}/changes"


def test_renaming_config_renames_folder(project):
    (project / "specworks.yml").rename(project / "context.yml")
    code, data = run_json("new", "add-login")
    assert data["path"] == "context/changes/add-login"


def test_unrelated_yml_is_not_a_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs.yml").write_text("site_name: my docs\n")
    code, data = run_json("context")
    assert code == 1 and data["root"] is None


def test_two_configs_in_one_folder_is_an_error(project):
    (project / "spec.yml").write_text("specworks: 1\n")
    code, data = run_json("context")
    assert code == 1 and "several specworks configs" in data["error"]


def test_old_dir_key_is_rejected(project):
    cfg = project / "specworks.yml"
    cfg.write_text(cfg.read_text() + "dir: spec\n")
    code, data = run_json("context")
    assert code == 1 and "'dir' is no longer a setting" in data["error"]


@pytest.mark.parametrize("folder", ["/abs", "../outside", ".", "", "docs/spec", ".hidden"])
def test_init_rejects_bad_dir(tmp_path, monkeypatch, folder):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--dir", folder])
    assert result.exit_code == 1
    assert list(tmp_path.glob("*.yml")) == []
