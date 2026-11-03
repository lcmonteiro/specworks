import shutil

import pytest

from helpers import init_repo, set_saved_tools
from specworks.core.config import load_config
from specworks.core.config_file import save_tools
from specworks.core.errors import ConfigError
from specworks.core.workspace import load_workspace
from support.modules import make_workspace, run, run_json


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    return make_workspace(tmp_path, monkeypatch)


# @ac AC-PROJ-008.1
def test_module_add_keeps_comments(workspace):
    assert "# Modules: sub-projects" in (workspace / ".specworks/config.yml").read_text()


# @ac AC-PROJ-003.7
def test_tools_in_a_modules_config_are_refused(workspace):
    set_saved_tools(workspace / "services/billing", "[claude]")
    code, data = run_json("context")
    assert code == 1 and "'tools'" in data["error"] and "top level" in data["error"], data


# @ac AC-PROJ-022.1
def test_saving_the_tools_keeps_the_comments(workspace):
    config = workspace / ".specworks/config.yml"
    before = config.read_text(encoding="utf-8")
    save_tools(workspace, ["claude", "copilot"])
    text = config.read_text(encoding="utf-8")
    assert "tools: [claude, copilot]" in text.splitlines()
    comments = [line for line in before.splitlines() if line.lstrip().startswith("#")]
    assert comments and all(line in text.splitlines() for line in comments)
    assert "  billing: services/billing" in text.splitlines()  # the other entries too
    assert load_config(workspace).tools == ["claude", "copilot"]


# @ac AC-PROJ-022.2
@pytest.mark.parametrize("saved", ["[claude]", "\n  - claude"], ids=["flow", "block"])
def test_saving_the_tools_replaces_the_saved_list(workspace, saved):
    config = workspace / ".specworks/config.yml"
    set_saved_tools(workspace, saved)
    save_tools(workspace, ["copilot"])
    lines = config.read_text(encoding="utf-8").splitlines()
    assert [line for line in lines if line.startswith("tools:")] == ["tools: [copilot]"]
    assert "  - claude" not in lines
    assert load_config(workspace).tools == ["copilot"]


# @ac AC-PROJ-022.3
def test_saving_the_tools_leaves_a_config_it_cannot_edit_unchanged(workspace):
    config = workspace / ".specworks/config.yml"
    set_saved_tools(workspace, "[claude]")
    config.write_text(config.read_text(encoding="utf-8") + "tools:\n  - claude\n", encoding="utf-8")  # a second `tools:` entry
    before = config.read_text(encoding="utf-8")
    with pytest.raises(ConfigError, match="by hand") as error:
        save_tools(workspace, ["copilot"])
    assert "tools" in str(error.value)
    assert config.read_text(encoding="utf-8") == before


# @ac AC-PROJ-004.2, AC-PROJ-006.1, AC-PROJ-007.1, AC-CLI-004.1
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
            "testsPath": "services/billing/tests/invoices",
            "hasSpec": False,
            "prefix": "BILLING-INVOICES",
            "deltaPath": "specs/billing/invoices/spec.md",
        }
    ]


# @ac AC-PROJ-001.5, AC-CLI-006.1
def test_new_goes_to_nearest_module(workspace, monkeypatch):
    (workspace / "services/billing/src").mkdir()
    monkeypatch.chdir(workspace / "services/billing/src")
    code, data = run_json("new", "add-refunds", "--no-branch")
    assert data["path"] == "services/billing/.specworks/changes/active/add-refunds"
    assert data["ref"] == "billing:add-refunds"


# @ac AC-PROJ-006.2
def test_missing_module_is_reported_not_fatal(workspace):
    (workspace / ".specworks/config.yml").write_text(
        (workspace / ".specworks/config.yml").read_text().replace("\nmodules:\n", "\nmodules:\n  ghost: vendor/ghost\n")
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
    (workspace / ".specworks/config.yml").write_text(
        (workspace / ".specworks/config.yml").read_text().replace("\nmodules:\n", "\nmodules:\n" + modules)
    )
    code, data = run_json("context")
    assert code == 1


# @ac AC-PROJ-005.1
def test_derived_prefixes_may_not_collide_across_modules(workspace):
    # billing:invoices derives BILLING-INVOICES; so would a top-level billing-invoices.
    cfg = workspace / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("capabilities: {}", "capabilities:\n  billing-invoices:\n    path: src/bi"))
    code, data = run_json("list")
    assert code == 1 and "both use the ID prefix BILLING-INVOICES" in data["error"]


# @ac AC-PROJ-026.4
def test_ac_proj_026_4_a_modules_own_branch_setting_is_ignored(workspace, monkeypatch):
    top, billing = workspace / ".specworks/config.yml", workspace / "services/billing/.specworks/config.yml"
    top.write_text(top.read_text() + "branch_per_change: false\n")
    billing.write_text(billing.read_text() + "branch_per_change: true\n")
    monkeypatch.chdir(workspace / "services/billing")
    ws = load_workspace()
    assert ws is not None and ws.current.name == "billing"
    assert ws.top.config.branch_per_change is False


# @ac AC-PROJ-007.2
def test_a_module_inherits_the_commands_it_does_not_set(workspace):
    top, billing = workspace / ".specworks/config.yml", workspace / "services/billing/.specworks/config.yml"
    top.write_text(top.read_text().replace("commands:\n  test:\n  lint:\n", "commands:\n  test: top-test\n  lint: top-lint\n"))
    billing.write_text(billing.read_text().replace("commands:\n  test:\n", "commands:\n  test: billing-test\n"))
    ws = load_workspace(workspace)
    assert ws is not None
    assert ws.commands(ws.module("billing")) == {"test": "billing-test", "lint": "top-lint"}
    assert ws.commands(ws.module("billing/tax")) == {"test": "billing-test", "lint": "top-lint"}


def set_capabilities(cfg, block):
    cfg.write_text(cfg.read_text().replace("capabilities: {}", "capabilities:\n" + block))


# @ac AC-PROJ-016.1
def test_two_capabilities_on_one_path_are_refused(workspace):
    set_capabilities(workspace / ".specworks/config.yml", "  auth:\n    path: src/auth\n  login:\n    path: src/auth/\n")
    code, data = run_json("context")
    assert code == 1 and "auth" in data["error"] and "login" in data["error"] and "src/auth/docs" in data["error"]


# @ac AC-PROJ-016.2
def test_capabilities_of_two_modules_on_one_folder_are_refused(workspace):
    set_capabilities(workspace / ".specworks/config.yml", "  top-invoices:\n    path: services/billing/src/invoices\n")
    code, data = run_json("context")
    assert code == 1 and "top-invoices" in data["error"] and "billing:invoices" in data["error"]


# @ac AC-PROJ-016.3
def test_nested_capability_paths_load(workspace):
    set_capabilities(workspace / ".specworks/config.yml", "  auth:\n    path: src/auth\n  admin:\n    path: src/auth/admin\n")
    code, data = run_json("context")
    docs = {c["name"]: c["docsPath"] for c in data["capabilities"]}
    assert code == 0 and docs["auth"] == "src/auth/docs" and docs["admin"] == "src/auth/admin/docs"


# @ac AC-PROJ-016.4
def test_capability_add_refuses_a_taken_path(workspace):
    run_json("capability", "add", "auth", "--path", "src/auth")
    before = (workspace / ".specworks/config.yml").read_text()
    code, data = run_json("capability", "add", "login", "--path", "src/auth")
    assert code == 1 and "auth" in data["error"] and "src/auth/docs" in data["error"]
    assert (workspace / ".specworks/config.yml").read_text() == before
    code, data = run_json("capability", "add", "login", "--path", "src\\auth\\")  # stored as src/auth
    assert code == 1 and "already used by auth" in data["error"]
    assert (workspace / ".specworks/config.yml").read_text() == before


def link_module(workspace, name, target):
    """Link the folder ``target`` as module ``name`` of the top level, through a symlink called ``name``."""
    try:
        (workspace / name).symlink_to(target, target_is_directory=True)
    except OSError:  # Windows without the symlink privilege
        pytest.skip("cannot create symlinks here")
    cfg = workspace / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("\nmodules:\n", f"\nmodules:\n  {name}: {name}\n", 1))


# @ac AC-PROJ-006.6
def test_a_module_that_leads_back_to_an_ancestor_is_refused(workspace):
    link_module(workspace, "loop", workspace)
    code, data = run_json("context")
    assert code == 1 and "module 'loop'" in data["error"] and "(top)" in data["error"]


# @ac AC-PROJ-006.7
def test_a_folder_linked_as_a_module_twice_is_refused(workspace):
    link_module(workspace, "other", workspace / "services/billing")
    code, data = run_json("context")
    assert code == 1 and "'billing'" in data["error"] and "'other'" in data["error"]


# @ac AC-PROJ-006.8
def test_a_module_listed_past_the_module_that_contains_it_is_refused(workspace):
    run("init", "services/billing/sub", "--no-link", "--no-skills")
    cfg = workspace / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("\nmodules:\n", "\nmodules:\n  sub: services/billing/sub\n", 1))
    code, data = run_json("context")
    assert code == 1 and "module 'sub'" in data["error"] and "module 'billing'" in data["error"]


# @ac AC-PROJ-006.9
@pytest.mark.parametrize("with_config", [True, False])
def test_a_module_outside_the_workspace_is_refused(workspace, tmp_path_factory, monkeypatch, with_config):
    outside = tmp_path_factory.mktemp("outside")
    if with_config:
        monkeypatch.chdir(outside)
        init_repo(outside)
        run("init", "--no-link", "--no-skills")
        monkeypatch.chdir(workspace)
    link_module(workspace, "ext", outside)
    code, data = run_json("context")
    assert code == 1 and "module 'ext'" in data["error"] and str(outside) in data["error"]


# @ac AC-PROJ-021.2
def test_an_old_module_names_the_module_and_the_move(workspace):
    billing = workspace / "services/billing"
    shutil.rmtree(billing / ".specworks")
    (billing / "spec.yml").write_text("specworks: 1\n")
    (billing / "spec/changes/active").mkdir(parents=True)
    code, data = run_json("context")
    assert code == 1
    error = data["error"]
    assert "module 'billing'" in error and "spec.yml" in error
    assert "move spec.yml to .specworks/config.yml and spec/ to .specworks/" in error
    assert (billing / "spec.yml").is_file() and not (billing / ".specworks").exists()  # nothing moved


# --- a module's docs folder and its architecture (REQ-PROJ-029) ----------------------


# @ac AC-PROJ-029.1
def test_ac_proj_029_1_the_top_levels_docs_folder_is_docs(workspace):
    ws = load_workspace(workspace)
    assert ws.rel(ws.top.docs_path) == "docs" and ws.rel(ws.top.architecture_path) == "docs/architecture.md"
    assert not (workspace / "docs").exists()  # the paths hold whether or not the folder is there


# @ac AC-PROJ-029.2
def test_ac_proj_029_2_a_module_uses_its_own_docs_dir(workspace):
    config = workspace / "services/billing/.specworks/config.yml"
    text = config.read_text(encoding="utf-8")
    assert "docs_dir: docs\n" in text
    config.write_text(text.replace("docs_dir: docs\n", "docs_dir: doc\n"), encoding="utf-8")
    ws = load_workspace(workspace)
    billing = ws.module("billing")
    assert ws.rel(billing.docs_path) == "services/billing/doc"
    assert ws.rel(billing.architecture_path) == "services/billing/doc/architecture.md"


# @ac AC-PROJ-029.3
def test_ac_proj_029_3_a_capability_on_the_modules_folder_shares_its_docs_folder(workspace):
    set_capabilities(workspace / ".specworks/config.yml", "  core:\n    path: .\n")
    code, data = run_json("context")
    assert code == 0, data
    assert {c["name"]: c["docsPath"] for c in data["capabilities"]}["core"] == "docs"
    ws = load_workspace(workspace)
    assert ws.rel(ws.top.docs_path) == "docs"
