"""`capability add --create`: the capability's code folder created with an empty `.gitkeep`."""

import pytest
from typer.testing import CliRunner

from helpers import init_repo, run_json
from specworks.cli import app
from specworks.core.workspace import load_workspace

runner = CliRunner()
CONFIG = ".specworks/config.yml"


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A project with the default config written by `init` and no capability."""
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["init", "--no-skills"])
    assert result.exit_code == 0, result.output
    return tmp_path


def registered(root, module=None):
    """The capability names of a module's config (the top level by default)."""
    ws = load_workspace(root)
    target = ws.module(module) if module is not None else ws.current
    return set(target.config.capabilities)


def files_in(folder):
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*") if p.is_file()}


# @ac AC-CLI-014.1
def test_ac_cli_014_1_a_missing_folder_is_created_with_an_empty_gitkeep(project):
    code, data = run_json("capability", "add", "auth", "--path", "src/auth", "--create")
    assert code == 0, data
    gitkeep = project / "src/auth/.gitkeep"
    assert gitkeep.is_file() and gitkeep.read_bytes() == b""
    assert "auth" in registered(project)
    assert data["created"] == "src/auth/.gitkeep"


# @ac AC-CLI-014.1
def test_ac_cli_014_1_the_text_output_names_the_gitkeep_created(project):
    result = runner.invoke(app, ["capability", "add", "auth", "--path", "src/auth", "--create"])
    assert result.exit_code == 0, result.output
    assert "created src/auth/.gitkeep" in result.output
    assert (project / "src/auth/.gitkeep").is_file()


# @ac AC-CLI-014.2
def test_ac_cli_014_2_an_existing_folder_is_left_as_it_is(project):
    folder = project / "src/auth"
    folder.mkdir(parents=True)
    (folder / "login.py").write_text("LOGIN = 1\n", encoding="utf-8")
    before = files_in(folder)
    code, data = run_json("capability", "add", "auth", "--path", "src/auth", "--create")
    assert code == 0, data
    assert "auth" in registered(project)
    assert not (folder / ".gitkeep").exists()
    assert files_in(folder) == before
    assert data["created"] is None


# @ac AC-CLI-014.3
def test_ac_cli_014_3_in_a_module_the_folder_is_under_the_module_root(project):
    assert runner.invoke(app, ["module", "add", "services/billing"]).exit_code == 0
    result = runner.invoke(app, ["capability", "add", "invoices", "--path", "src/invoices", "--module", "billing", "--create"])
    assert result.exit_code == 0, result.output
    assert (project / "services/billing/src/invoices/.gitkeep").is_file()
    assert not (project / "src/invoices").exists()
    assert "invoices" in registered(project, "billing")
    assert "invoices" not in registered(project)
    assert "created services/billing/src/invoices/.gitkeep" in result.output  # relative to the workspace root


# @ac AC-CLI-014.4
def test_ac_cli_014_4_a_refused_capability_creates_nothing(project):
    code, data = run_json("capability", "add", "auth", "--path", "src/auth")  # uses the prefix AUTH
    assert code == 0, data
    before = (project / CONFIG).read_text(encoding="utf-8")
    code, data = run_json("capability", "add", "auth2", "--path", "src/auth2", "--prefix", "AUTH", "--create")
    assert code == 1 and "AUTH is already used by auth" in data["error"]
    assert not (project / "src/auth2").exists()
    assert (project / CONFIG).read_text(encoding="utf-8") == before


# @ac AC-CLI-014.5
def test_ac_cli_014_5_a_path_that_is_a_file_is_refused(project):
    (project / "src").mkdir()
    (project / "src/auth").write_bytes(b"not a folder\n")
    before = (project / CONFIG).read_text(encoding="utf-8")
    code, data = run_json("capability", "add", "auth", "--path", "src/auth", "--create")
    assert code == 1, data
    assert "exists and is not a folder" in data["error"] and "src/auth" in data["error"]
    assert (project / "src/auth").read_bytes() == b"not a folder\n"
    assert (project / CONFIG).read_text(encoding="utf-8") == before
    assert "auth" not in registered(project)


# @ac AC-CLI-014.6
def test_ac_cli_014_6_without_create_no_folder_is_created(project):
    result = runner.invoke(app, ["capability", "add", "auth", "--path", "src/auth"])
    assert result.exit_code == 0, result.output
    assert "auth" in registered(project)
    assert not (project / "src/auth").exists()
    assert "created" not in result.output


# @ac AC-CLI-014.6
def test_ac_cli_014_6_without_create_the_json_names_nothing_created(project):
    code, data = run_json("capability", "add", "auth", "--path", "src/auth")
    assert code == 0, data
    assert "created" in data and data["created"] is None
    assert not (project / "src/auth").exists()
