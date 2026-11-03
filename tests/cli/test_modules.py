import pytest

from specworks.cli import app
from specworks.core.workspace import load_workspace
from support.modules import make_workspace, run, run_json, runner


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    return make_workspace(tmp_path, monkeypatch)


# @ac AC-CLI-005.1
def test_module_add_links_parent_and_creates_module(workspace):
    assert "  billing: services/billing\n" in (workspace / ".specworks/config.yml").read_text()
    assert "  tax: tax\n" in (workspace / "services/billing/.specworks/config.yml").read_text()
    assert (workspace / "services/billing/.specworks/changes/active").is_dir()
    assert (workspace / "services/billing/.specworks/changes/archive").is_dir()
    assert (workspace / "services/billing/.specworks/config.yml").read_text().startswith("specworks: 1\n")
    assert not list((workspace / "services/billing").glob("*.yml"))  # nothing at the module's root


# @ac AC-CLI-004.4
def test_module_list_shows_tree(workspace):
    code, data = run_json("module", "list")
    assert [m["name"] for m in data["modules"]] == ["(top)", "billing", "billing/tax"]
    assert data["modules"][0]["current"] is True


# @ac AC-CLI-006.1
def test_new_with_module_option(workspace):
    code, data = run_json("new", "add-vat", "--module", "billing/tax", "--no-branch")
    assert data["path"] == "services/billing/tax/.specworks/changes/active/add-vat"
    code, data = run_json("new", "x", "--module", "nope", "--no-branch")
    assert code == 1 and "unknown module" in data["error"]


# @ac AC-CLI-002.1
def test_bare_change_name_resolves_across_modules(workspace):
    run_json("new", "add-vat", "--module", "billing/tax", "--no-branch")
    code, data = run_json("status", "--change", "add-vat")
    assert code == 0 and data["ref"] == "billing/tax:add-vat"


# @ac AC-CLI-002.2
def test_ambiguous_change_name_needs_module_prefix(workspace, monkeypatch):
    run_json("new", "cleanup", "--module", "billing", "--no-branch")
    run_json("new", "cleanup", "--module", "billing/tax", "--no-branch")
    code, data = run_json("status", "--change", "cleanup")
    assert code == 1 and "billing:cleanup" in data["error"] and "billing/tax:cleanup" in data["error"]
    code, data = run_json("status", "--change", "billing/tax:cleanup")
    assert code == 0 and data["module"] == "billing/tax"


# @ac AC-CLI-002.3
def test_current_module_wins_for_bare_name(workspace, monkeypatch):
    run_json("new", "cleanup", "--no-branch")
    run_json("new", "cleanup", "--module", "billing", "--no-branch")
    code, data = run_json("status", "--change", "cleanup")
    assert data["module"] == "(top)"


# @ac AC-CLI-004.2
def test_list_all_includes_every_module(workspace):
    run_json("new", "top-change", "--no-branch")
    run_json("new", "bill-change", "--module", "billing", "--no-branch")
    code, data = run_json("list")
    assert [c["ref"] for c in data["changes"]] == ["top-change"]
    code, data = run_json("list", "--all")
    assert [c["ref"] for c in data["changes"]] == ["top-change", "billing:bill-change"]


# @ac AC-CLI-001.3
def test_init_prints_paths_relative_to_the_workspace_root(workspace):
    output = run("init", "libs/auth", "--name", "auth", "--no-skills")
    assert "created libs/auth/.specworks/config.yml\nready   libs/auth/.specworks/changes/active/\nlinked  as module 'auth'" in output
    assert str(workspace) not in output


# @ac AC-CLI-003.3
def test_init_no_link_keeps_project_independent(workspace, monkeypatch):
    run("init", "tools/other", "--no-link", "--no-skills")
    assert "tools/other" not in (workspace / ".specworks/config.yml").read_text()
    monkeypatch.chdir(workspace / "tools/other")
    code, data = run_json("context")
    assert data["root"] == str(workspace / "tools/other")
    assert data["module"] == "(top)"


# @ac AC-CLI-005.2
def test_module_add_rejects_a_folder_with_an_old_style_config(workspace):
    other = workspace / "libs/legacy"
    other.mkdir(parents=True)
    (other / "docs.yml").write_text("specworks: 1\n")
    code, data = run_json("module", "add", "libs/legacy")
    assert code == 1 and "docs.yml" in data["error"]
    assert "move docs.yml to .specworks/config.yml and docs/ to .specworks/" in data["error"]  # the old-layout error
    assert not (other / ".specworks").exists()
    assert "legacy: libs/legacy" not in (workspace / ".specworks/config.yml").read_text()


# @ac AC-CLI-003.2
def test_init_in_a_nested_module_reports_its_full_name(workspace, monkeypatch):
    monkeypatch.chdir(workspace / "services/billing")
    assert "as module 'billing/vat'" in run("init", "vat", "--no-skills")


# @ac AC-CLI-005.3
def test_module_add_refuses_a_folder_outside_the_project(workspace, tmp_path_factory):
    outside = tmp_path_factory.mktemp("elsewhere")
    for path in (str(outside), "."):
        code, data = run_json("module", "add", path)
        assert code == 1 and "must be a folder inside" in data["error"], path
    assert "elsewhere" not in (workspace / ".specworks/config.yml").read_text()


# @ac AC-CLI-005.6
def test_module_add_links_to_the_module_that_contains_the_folder(workspace):
    top_before = (workspace / ".specworks/config.yml").read_text()
    code, data = run_json("module", "add", "services/billing/sub")
    assert code == 0 and data["name"] == "billing/sub"
    assert "  sub: sub\n" in (workspace / "services/billing/.specworks/config.yml").read_text()
    assert (workspace / ".specworks/config.yml").read_text() == top_before
    assert "billing/sub" in run("module", "list")


# @ac AC-CLI-005.7
def test_module_add_refuses_a_folder_around_a_module(workspace):
    configs = {p: p.read_text() for p in workspace.rglob(".specworks/config.yml")}
    code, data = run_json("module", "add", "services")
    assert code == 1 and "module 'billing'" in data["error"]
    assert {p: p.read_text() for p in workspace.rglob(".specworks/config.yml")} == configs
    assert not (workspace / "services/.specworks").exists()
    assert load_workspace(workspace) is not None


# @ac AC-CLI-003.6
def test_init_refuses_a_folder_around_a_module(workspace):
    configs = {p: p.read_text() for p in workspace.rglob(".specworks/config.yml")}
    result = runner.invoke(app, ["init", "services", "--no-skills"])
    assert result.exit_code == 1 and "module 'billing'" in result.output
    assert {p: p.read_text() for p in workspace.rglob(".specworks/config.yml")} == configs
    assert not (workspace / "services/.specworks").exists()
    assert load_workspace(workspace) is not None


# @ac AC-CLI-004.6
def test_ac_cli_004_6_context_shows_each_modules_docs_folder(workspace):
    (workspace / "docs").mkdir()
    (workspace / "docs/architecture.md").write_text("# Architecture\n", encoding="utf-8")
    code, data = run_json("context")
    assert code == 0, data
    modules = {m["name"]: m for m in data["modules"]}
    assert (modules["(top)"]["docsPath"], modules["(top)"]["hasArchitecture"]) == ("docs", True)
    assert (modules["billing"]["docsPath"], modules["billing"]["hasArchitecture"]) == ("services/billing/docs", False)
