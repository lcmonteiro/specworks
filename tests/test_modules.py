import json

import pytest
from typer.testing import CliRunner

from specworks.cli import app
from specworks.core.workspace import load_workspace
from specworks.specs.trace import scan_tags

runner = CliRunner()


def run(*args):
    result = runner.invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return result.output


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    return result.exit_code, json.loads(result.output)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Top-level project with module billing (services/billing) and nested module billing/tax."""
    monkeypatch.chdir(tmp_path)
    run("init", "--dir", "spec")
    (tmp_path / "spec.yml").write_text(
        (tmp_path / "spec.yml").read_text().replace("context: |\n", "context: |\n  Company-wide: Python 3.12\n")
    )
    run("module", "add", "services/billing")
    billing = tmp_path / "services/billing"
    (billing / "spec.yml").write_text(
        (billing / "spec.yml").read_text()
        .replace("context: |\n", "context: |\n  Billing: money is Decimal\n")
        .replace("capabilities: {}", "capabilities:\n  invoices:\n    path: src/invoices")
    )
    monkeypatch.chdir(billing)
    run("module", "add", "tax")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_module_add_links_parent_and_creates_module(workspace):
    assert "  billing: services/billing\n" in (workspace / "spec.yml").read_text()
    assert "  tax: tax\n" in (workspace / "services/billing/spec.yml").read_text()
    assert (workspace / "services/billing/spec/changes/archive").is_dir()
    assert (workspace / "services/billing/spec.yml").read_text().startswith("specworks: 1\n")
    assert not (workspace / "services/billing/specworks.yml").exists()


# @ac AC-PROJ-008.1
def test_module_add_keeps_comments(workspace):
    assert "# Modules: sub-projects" in (workspace / "spec.yml").read_text()


def test_module_list_shows_tree(workspace):
    code, data = run_json("module", "list")
    assert [m["name"] for m in data["modules"]] == ["(top)", "billing", "billing/tax"]
    assert data["modules"][0]["current"] is True


# @ac AC-PROJ-004.2, AC-PROJ-006.1, AC-PROJ-007.1
def test_context_inside_module_inherits_and_sees_whole_workspace(workspace, monkeypatch):
    monkeypatch.chdir(workspace / "services/billing/tax")
    code, data = run_json("context")
    assert code == 0
    assert data["root"] == str(workspace)
    assert data["module"] == "billing/tax"
    assert [c["module"] for c in data["contextChain"]] == ["(top)", "billing"]
    assert data["context"].index("Company-wide") < data["context"].index("Billing")
    assert data["capabilities"] == [
        {
            "name": "billing:invoices",
            "module": "billing",
            "path": "services/billing/src/invoices",
            "description": "",
            "docsPath": "services/billing/src/invoices/docs",
            "hasSpec": False,
            "prefix": "BILLING-INVOICES",
            "deltaPath": "specs/billing/invoices/spec.md",
        }
    ]


# @ac AC-PROJ-001.5
def test_new_goes_to_nearest_module(workspace, monkeypatch):
    (workspace / "services/billing/src").mkdir()
    monkeypatch.chdir(workspace / "services/billing/src")
    code, data = run_json("new", "add-refunds")
    assert data["path"] == "services/billing/spec/changes/add-refunds"
    assert data["ref"] == "billing:add-refunds"


def test_new_with_module_option(workspace):
    code, data = run_json("new", "add-vat", "--module", "billing/tax")
    assert data["path"] == "services/billing/tax/spec/changes/add-vat"
    code, data = run_json("new", "x", "--module", "nope")
    assert code == 1 and "unknown module" in data["error"]


def test_bare_change_name_resolves_across_modules(workspace):
    run_json("new", "add-vat", "--module", "billing/tax")
    code, data = run_json("status", "--change", "add-vat")
    assert code == 0 and data["ref"] == "billing/tax:add-vat"


def test_ambiguous_change_name_needs_module_prefix(workspace, monkeypatch):
    run_json("new", "cleanup", "--module", "billing")
    run_json("new", "cleanup", "--module", "billing/tax")
    code, data = run_json("status", "--change", "cleanup")
    assert code == 1 and "billing:cleanup" in data["error"] and "billing/tax:cleanup" in data["error"]
    code, data = run_json("status", "--change", "billing/tax:cleanup")
    assert code == 0 and data["module"] == "billing/tax"


def test_current_module_wins_for_bare_name(workspace, monkeypatch):
    run_json("new", "cleanup")
    run_json("new", "cleanup", "--module", "billing")
    code, data = run_json("status", "--change", "cleanup")
    assert data["module"] == "(top)"


def test_list_all_includes_every_module(workspace):
    run_json("new", "top-change")
    run_json("new", "bill-change", "--module", "billing")
    code, data = run_json("list")
    assert [c["ref"] for c in data["changes"]] == ["top-change"]
    code, data = run_json("list", "--all")
    assert [c["ref"] for c in data["changes"]] == ["top-change", "billing:bill-change"]


# @ac AC-FLOW-002.2
def test_instructions_in_module_use_inherited_context(workspace):
    run_json("new", "add-refunds", "--module", "billing")
    code, data = run_json("instructions", "refinement", "--change", "billing:add-refunds")
    assert data["outputPath"] == "services/billing/spec/changes/add-refunds/refinement.md"
    assert "Company-wide" in data["context"] and "Billing" in data["context"]


def test_init_in_subfolder_links_to_parent(workspace):
    run("init", "libs/auth", "--name", "auth")
    assert "  auth: libs/auth\n" in (workspace / "spec.yml").read_text()
    assert not (workspace / "libs/auth/.claude").exists()  # skills stay at the workspace root
    code, data = run_json("module", "list")
    assert "auth" in [m["name"] for m in data["modules"]]


def test_init_prints_paths_relative_to_the_workspace_root(workspace):
    output = run("init", "libs/auth", "--name", "auth", "--no-skills")
    assert "created libs/auth/spec.yml\nready   libs/auth/spec/changes/\nlinked  as module 'auth'" in output
    assert str(workspace) not in output


def test_init_no_link_keeps_project_independent(workspace, monkeypatch):
    run("init", "tools/other", "--no-link", "--no-skills")
    assert "tools/other" not in (workspace / "spec.yml").read_text()
    monkeypatch.chdir(workspace / "tools/other")
    code, data = run_json("context")
    assert data["root"] == str(workspace / "tools/other")
    assert data["module"] == "(top)"


# @ac AC-PROJ-006.2
def test_missing_module_is_reported_not_fatal(workspace):
    (workspace / "spec.yml").write_text(
        (workspace / "spec.yml").read_text().replace("\nmodules:\n", "\nmodules:\n  ghost: vendor/ghost\n")
    )
    code, data = run_json("context")
    assert code == 0
    assert data["missingModules"] == [{"name": "ghost", "path": "vendor/ghost"}]


# @ac AC-PROJ-008.3
def test_duplicate_module_rejected(workspace):
    code, data = run_json("module", "add", "services/billing", "--name", "billing2")
    assert code == 1 and "already linked" in data["error"]
    code, data = run_json("module", "add", "other", "--name", "billing")
    assert code == 1 and "already exists" in data["error"]


# @ac AC-PROJ-003.1
@pytest.mark.parametrize("modules", ["  bad: ../x\n", "  Bad_Name: x\n"])
def test_invalid_module_entries_rejected(workspace, modules):
    (workspace / "spec.yml").write_text(
        (workspace / "spec.yml").read_text().replace("\nmodules:\n", "\nmodules:\n" + modules)
    )
    code, data = run_json("context")
    assert code == 1


@pytest.mark.parametrize("folder", ["spec", "docs", "context", "specworks"])
def test_modules_use_the_top_level_folder_name(tmp_path, monkeypatch, folder):
    monkeypatch.chdir(tmp_path)
    run("init", "--dir", folder)
    run("module", "add", "services/billing")
    run("init", "libs/auth")
    for module in ("services/billing", "libs/auth"):
        assert (tmp_path / module / f"{folder}.yml").is_file()
        assert (tmp_path / module / folder / "changes/archive").is_dir()
    code, data = run_json("module", "list")
    assert [m["dir"] for m in data["modules"]] == [folder, f"services/billing/{folder}", f"libs/auth/{folder}"]


def test_nested_module_uses_the_top_level_folder_name(workspace):
    assert (workspace / "services/billing/tax/spec/changes").is_dir()
    code, data = run_json("new", "add-vat", "--module", "billing/tax")
    assert data["path"] == "services/billing/tax/spec/changes/add-vat"


# @ac AC-PROJ-006.3
def test_module_with_different_config_name_is_an_error(workspace):
    billing = workspace / "services/billing"
    (billing / "spec.yml").rename(billing / "docs.yml")
    code, data = run_json("context")
    assert code == 1
    assert "module 'billing' uses docs.yml" in data["error"] and "workspace uses spec.yml" in data["error"]


def test_init_module_with_different_dir_is_rejected(workspace):
    result = runner.invoke(app, ["init", "libs/auth", "--dir", "docs"])
    assert result.exit_code == 1
    assert not (workspace / "libs/auth").exists()
    assert "auth: libs/auth" not in (workspace / "spec.yml").read_text()


def test_init_no_link_may_use_another_dir(workspace):
    run("init", "tools/other", "--dir", "docs", "--no-link", "--no-skills")
    assert (workspace / "tools/other/docs.yml").is_file()
    assert (workspace / "tools/other/docs/changes").is_dir()


def test_module_add_rejects_existing_config_with_other_dir(workspace):
    other = workspace / "libs/legacy"
    other.mkdir(parents=True)
    (other / "docs.yml").write_text("specworks: 1\n")
    code, data = run_json("module", "add", "libs/legacy")
    assert code == 1 and "uses docs.yml" in data["error"]
    assert not (other / "spec.yml").exists()
    assert "legacy: libs/legacy" not in (workspace / "spec.yml").read_text()


def test_test_globs_are_relative_to_their_module_and_apply_only_to_it(workspace):
    billing = workspace / "services/billing"
    cfg = billing / "spec.yml"
    cfg.write_text(cfg.read_text().replace("test_globs: []", 'test_globs: ["qa/*.py"]'))
    (billing / "qa").mkdir()
    (billing / "qa/check_invoices.py").write_text("# @ac AC-BILLING-INVOICES-001.1\n")  # specworks: ignore-tags
    (billing / "src").mkdir()
    (billing / "src/invoices.py").write_text("# @req REQ-BILLING-INVOICES-001\n")  # specworks: ignore-tags
    (workspace / "tests").mkdir()
    (workspace / "tests/test_top.py").write_text("# @ac AC-TOP-001.1\n")  # specworks: ignore-tags
    (workspace / "app.py").write_text("# @req REQ-TOP-001\n")  # specworks: ignore-tags
    ws = load_workspace(workspace)
    assert ws is not None
    found = {(t.file, t.is_test) for t in scan_tags(ws)}
    # billing's qa/ files are its tests (its code is still scanned: test_globs only mark tests);
    # the top level keeps its default (scan all, tests by name).
    assert found == {
        ("services/billing/qa/check_invoices.py", True),
        ("services/billing/src/invoices.py", False),
        ("tests/test_top.py", True),
        ("app.py", False),
    }


def test_init_in_a_nested_module_reports_its_full_name(workspace, monkeypatch):
    monkeypatch.chdir(workspace / "services/billing")
    assert "as module 'billing/vat'" in run("init", "vat", "--no-skills")


# @ac AC-PROJ-005.1
def test_derived_prefixes_may_not_collide_across_modules(workspace):
    # billing:invoices derives BILLING-INVOICES; so would a top-level billing-invoices.
    cfg = workspace / "spec.yml"
    cfg.write_text(cfg.read_text().replace("capabilities: {}", "capabilities:\n  billing-invoices:\n    path: src/bi"))
    code, data = run_json("list")
    assert code == 1 and "both use the ID prefix BILLING-INVOICES" in data["error"]


def test_a_new_capability_of_a_module_is_registered_with_module(workspace):
    run("new", "add-refunds")
    delta = workspace / "spec/changes/add-refunds/specs/billing/refunds/spec.md"
    delta.parent.mkdir(parents=True)
    delta.write_text("## Purpose\nRefunds.\n\n## ADDED Requirements\n\n### Requirement: REQ-BILLING-REFUNDS-001 Refund\nThe system SHALL refund.\n\n"
                     "#### Scenario: AC-BILLING-REFUNDS-001.1 Refunded\n- **WHEN** x\n- **THEN** y\n")
    code, data = run_json("check", "--change", "add-refunds")
    assert any(i["message"].endswith("specworks capability add refunds --path <code path> --module billing") for i in data["issues"])


# @ac AC-PROJ-007.2
def test_a_module_inherits_the_commands_it_does_not_set(workspace):
    top, billing = workspace / "spec.yml", workspace / "services/billing/spec.yml"
    top.write_text(top.read_text().replace("commands:\n  test:\n  lint:\n", "commands:\n  test: top-test\n  lint: top-lint\n"))
    billing.write_text(billing.read_text().replace("commands:\n  test:\n", "commands:\n  test: billing-test\n"))
    ws = load_workspace(workspace)
    assert ws is not None
    assert ws.commands(ws.module("billing")) == {"test": "billing-test", "lint": "top-lint"}
    assert ws.commands(ws.module("billing/tax")) == {"test": "billing-test", "lint": "top-lint"}
