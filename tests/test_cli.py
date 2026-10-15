import json
import re

import pytest
from typer.testing import CliRunner

from specworks.cli import app, main

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
    assert (project / ".claude/skills/specworks-refine/SKILL.md").is_file()


def test_init_prints_paths_relative_to_the_project_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--dir", "spec", "--no-skills"])
    assert result.exit_code == 0 and result.output == "created spec.yml\nready   spec/changes/\n"


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
    code, data = run_json("phase", "add-login", "specify")
    assert code == 0 and data["phase"] == "specify"
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


@pytest.mark.parametrize(
    "setting, message",
    [
        ("capabilities: [user-auth]", "'capabilities' must be a mapping"),
        ("capabilities:\n  user-auth: [src/auth]", "capability 'user-auth' needs a 'path'"),
        ("test_globs: 'tests/**'", 'test_globs: ["tests/**"]'),
        ("source_globs: [src/**, 3]", "'source_globs' must be a list of glob strings"),
        ("docs_dir: ../../outside", "'docs_dir' must be a relative folder inside the project"),
        ("docs_dir: /etc", "'docs_dir' must be a relative folder inside the project"),
        ("docs_dir: 3", "'docs_dir' must be a non-empty folder name"),
    ],
)
def test_malformed_config_is_a_clear_error(project, setting, message):
    cfg = project / "specworks.yml"
    key = setting.split(":", 1)[0]
    text = "\n".join(line for line in cfg.read_text().splitlines() if not line.startswith(f"{key}:"))
    cfg.write_text(f"{text}\n{setting}\n")
    code, data = run_json("context")
    assert code == 1 and message in data["error"], data


def test_nested_docs_dir_is_allowed(project):
    cfg = project / "specworks.yml"
    cfg.write_text(cfg.read_text().replace("docs_dir: docs", "docs_dir: docs/specworks"))
    code, data = run_json("context")
    assert code == 0, data


@pytest.mark.parametrize("folder", ["/abs", "../outside", ".", "", "docs/spec", ".hidden"])
def test_init_rejects_bad_dir(tmp_path, monkeypatch, folder):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--dir", folder])
    assert result.exit_code == 1
    assert list(tmp_path.glob("*.yml")) == []


def test_phases_follow_the_workflow(project):
    run_json("new", "add-login")
    code, data = run_json("status", "--change", "add-login")
    assert data["phases"] == ["refine", "specify", "design", "test", "code", "review", "validate", "close", "done"]
    for phase in ("code", "specify", "done"):  # moving back is allowed
        code, data = run_json("phase", "add-login", phase)
        assert code == 0 and data["phase"] == phase


def test_skills_are_installed_with_specworks_prefix(project):
    skills = sorted(p.name for p in (project / ".claude/skills").iterdir())
    assert skills and all(name.startswith("specworks-") for name in skills)
    text = (project / ".claude/skills/specworks-refine/SKILL.md").read_text()
    assert "name: specworks-refine" in text and "sw-" not in text


def test_changes_saved_with_old_phase_names_still_load(project):
    run_json("new", "old-change")
    meta = project / "specworks/changes/old-change/.change.yaml"
    for old, new in (("propose", "specify"), ("interface", "design"), ("implement", "code"), ("verify", "validate")):
        meta.write_text(re.sub(r"(?m)^phase: .*$", f"phase: {old}", meta.read_text()))
        code, data = run_json("status", "--change", "old-change")
        assert code == 0 and data["phase"] == new


@pytest.mark.parametrize(
    "meta, message",
    [
        ("- a\n- list\n", "specworks/changes/add-login/.change.yaml must be a mapping (name, created, phase), got list"),
        ("phase: [unclosed\n", "cannot read specworks/changes/add-login/.change.yaml"),
        ("phase: shipping\n", "change 'add-login' has unknown phase 'shipping' in specworks/changes/add-login/.change.yaml"),
    ],
    ids=["list", "bad-yaml", "unknown-phase"],
)
def test_a_broken_change_file_is_an_error_not_a_crash(project, monkeypatch, capsys, meta, message):
    run_json("new", "add-login")
    (project / "specworks/changes/add-login/.change.yaml").write_text(meta)
    # Naming the change reports the broken file, not "not found".
    code, data = run_json("status", "--change", "add-login")
    assert code == 1 and message in data["error"]
    # Commands that list every change go through main(), which turns the error into a message.
    monkeypatch.setattr("sys.argv", ["specworks", "list", "--json"])
    with pytest.raises(SystemExit) as exit_info:
        main()
    assert exit_info.value.code == 1 and message in json.loads(capsys.readouterr().out)["error"]
    monkeypatch.setattr("sys.argv", ["specworks", "context"])
    with pytest.raises(SystemExit) as exit_info:
        main()
    err = capsys.readouterr().err
    assert exit_info.value.code == 1 and err.startswith("error: ") and message in err
