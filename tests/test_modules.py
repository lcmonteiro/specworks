import pytest

from helpers import init_repo
from specworks.core.workspace import load_workspace
from specworks.specs.trace import scan_tags
from support.modules import make_workspace, run, run_json


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    return make_workspace(tmp_path, monkeypatch)


def test_every_module_uses_the_fixed_workflow_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    run("init")
    run("module", "add", "services/billing")
    run("init", "libs/auth")
    for module in ("services/billing", "libs/auth"):
        assert (tmp_path / module / ".specworks/config.yml").is_file()
        assert (tmp_path / module / ".specworks/changes/active").is_dir()
        assert (tmp_path / module / ".specworks/changes/archive").is_dir()
    code, data = run_json("module", "list")
    assert [m["dir"] for m in data["modules"]] == [".specworks", "services/billing/.specworks", "libs/auth/.specworks"]


def test_nested_module_uses_the_top_level_folder_name(workspace):
    assert (workspace / "services/billing/tax/.specworks/changes/active").is_dir()
    code, data = run_json("new", "add-vat", "--module", "billing/tax", "--no-branch")
    assert data["path"] == "services/billing/tax/.specworks/changes/active/add-vat"


def test_test_globs_are_relative_to_their_module_and_apply_only_to_it(workspace):
    billing = workspace / "services/billing"
    cfg = billing / ".specworks/config.yml"
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


def test_a_new_capability_of_a_module_is_registered_with_module(workspace):
    run("new", "add-refunds", "--no-branch")
    delta = workspace / ".specworks/changes/active/add-refunds/specs/billing/refunds/spec.md"
    delta.parent.mkdir(parents=True)
    delta.write_text("## Purpose\nRefunds.\n\n## ADDED Requirements\n\n### Requirement: REQ-BILLING-REFUNDS-001 Refund\nThe system SHALL refund.\n\n"
                     "#### Scenario: AC-BILLING-REFUNDS-001.1 Refunded\n- **WHEN** x\n- **THEN** y\n")
    code, data = run_json("check", "--change", "add-refunds")
    assert any(i["message"].endswith("specworks capability add refunds --path <code path> --module billing") for i in data["issues"])
