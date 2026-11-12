import json
import re

import pytest

from helpers import init_repo, set_saved_tools
from specworks.cli import app, main
from specworks.core.config import TOOL_IDS, load_config
from support.cli import make_project, run_json, runner


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


# @ac AC-PROJ-001.4, AC-CLI-001.1
def test_context_without_project_reports_null_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code, data = run_json("context")
    assert code == 1
    assert data["root"] is None


# @ac AC-PROJ-010.1
def test_new_change_starts_in_refine_phase(project):
    code, data = run_json("new", "add-login", "--no-branch")
    assert code == 0
    assert data["phase"] == "refine"
    code, data = run_json("list")
    assert [c["name"] for c in data["changes"]] == ["add-login"]


# @ac AC-PROJ-010.2
@pytest.mark.parametrize("name", ["Add_Login", "add login", "x--y", "archive-"])
def test_new_rejects_non_kebab_names(project, name):
    code, data = run_json("new", name, "--no-branch")
    assert code == 1
    assert "kebab-case" in data["error"]


# @ac AC-PROJ-010.3
def test_new_rejects_duplicates(project):
    run_json("new", "add-login", "--no-branch")
    code, data = run_json("new", "add-login", "--no-branch")
    assert code == 1 and "already exists" in data["error"]


# @ac AC-PROJ-020.1
def test_active_changes_are_listed_from_the_active_folder(project):
    code, data = run_json("new", "add-login", "--no-branch")
    assert code == 0 and data["path"] == ".specworks/changes/active/add-login"
    assert (project / ".specworks/changes/active/add-login/.change.yaml").is_file()
    assert not (project / ".specworks/changes/add-login").exists()
    code, data = run_json("list")
    assert code == 0 and [(c["name"], c["path"]) for c in data["changes"]] == [("add-login", ".specworks/changes/active/add-login")]


# @ac AC-PROJ-020.2
def test_a_loose_folder_under_changes_is_not_a_change(project):
    loose = project / ".specworks/changes/add-login"
    loose.mkdir()
    (loose / ".change.yaml").write_text("name: add-login\ncreated: '2026-01-01T10:00:00'\nphase: refine\n")
    code, data = run_json("list")
    assert code == 0 and data["changes"] == []
    code, data = run_json("status", "--change", "add-login")
    assert code == 1 and "not found" in data["error"]


# @ac AC-PROJ-010.4
@pytest.mark.parametrize("name", ["active", "archive"])
def test_new_refuses_the_reserved_folder_names(project, name):
    code, data = run_json("new", name, "--no-branch")
    assert code == 1 and "reserved" in data["error"] and name in data["error"]
    assert not (project / ".specworks/changes/active" / name).exists()


# @ac AC-PROJ-011.2
def test_only_close_makes_a_change_done(project):
    run_json("new", "add-login", "--no-branch")
    code, data = run_json("phase", "done", "--change", "add-login")
    assert code == 1 and "only through `specworks close`" in data["error"]
    code, data = run_json("list")
    assert [c["phase"] for c in data["changes"]] == ["refine"]


# @ac AC-PROJ-001.1, AC-PROJ-009.1
def test_init_writes_the_config_in_the_fixed_workflow_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    assert (tmp_path / ".specworks/config.yml").read_text().startswith("specworks: 1\n")
    assert list(tmp_path.glob("*.yml")) == []  # nothing at the project's root
    assert (tmp_path / ".specworks/changes/active").is_dir()
    assert (tmp_path / ".specworks/changes/archive").is_dir()
    code, data = run_json("new", "add-login", "--no-branch")
    assert code == 0 and data["path"] == ".specworks/changes/active/add-login"
    assert (tmp_path / ".specworks/changes/active/add-login/.change.yaml").is_file()
    code, data = run_json("context")
    assert data["dir"] == ".specworks" and data["changesDir"] == ".specworks/changes/active"


# @ac AC-PROJ-001.2
@pytest.mark.parametrize("content", [b"site_name: my docs\n", b"\xff\xfe specworks: 1\n"], ids=["no-marker", "not-utf8"])
def test_a_config_yml_without_the_marker_is_not_a_project(tmp_path, monkeypatch, content):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".specworks").mkdir()
    (tmp_path / ".specworks/config.yml").write_bytes(content)
    code, data = run_json("context")
    assert code == 1 and data["root"] is None


# @ac AC-PROJ-001.6
@pytest.mark.parametrize("name", ["docs.yml", "mkdocs.yml", "config.yml"])
def test_other_yaml_files_are_not_configs(tmp_path, monkeypatch, name):
    monkeypatch.chdir(tmp_path)
    (tmp_path / name).write_text("site_name: my docs\n")
    code, data = run_json("context")
    assert code == 1 and data["root"] is None


def old_layout(root):
    """
    A project in the old layout: ``spec.yml`` with the marker and its ``spec/`` folder.
    """
    (root / "spec.yml").write_text("specworks: 1\ncapabilities: {}\n")
    (root / "spec/changes/active/add-login").mkdir(parents=True)
    (root / "spec/changes/active/add-login/.change.yaml").write_text("name: add-login\ncreated: '2026-01-01T10:00:00'\nphase: refine\n")


# @ac AC-PROJ-021.1
@pytest.mark.parametrize("where", [".", "src/auth"])
def test_an_old_project_names_the_move_and_moves_nothing(tmp_path, monkeypatch, where):
    old_layout(tmp_path)
    (tmp_path / where).mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path / where)
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    code, data = run_json("list")
    assert code == 1
    error = data["error"]
    assert "spec.yml" in error and "move spec.yml to .specworks/config.yml and spec/ to .specworks/" in error
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")) == before
    assert not (tmp_path / ".specworks").exists()


# @ac AC-PROJ-021.3
def test_a_new_project_wins_over_a_leftover_old_config(project):
    (project / "spec.yml").write_text("specworks: 1\nbogus: true\n")  # old and broken: never read
    code, data = run_json("context")
    assert code == 0 and data["root"] == str(project)
    assert data["dir"] == ".specworks" and data["changesDir"] == ".specworks/changes/active"
    code, data = run_json("new", "add-login", "--no-branch")
    assert code == 0 and data["path"] == ".specworks/changes/active/add-login"


# @ac AC-PROJ-021.4
@pytest.mark.parametrize("flags", [[], ["--no-link"]], ids=["link", "no-link"])
def test_init_in_an_old_project_names_the_move_and_writes_nothing(tmp_path, monkeypatch, flags):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    old_layout(tmp_path)
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if ".git" not in p.relative_to(tmp_path).parts)
    result = runner.invoke(app, ["init", *flags])  # skills not turned off: none may be written either
    assert result.exit_code == 1
    assert "spec.yml" in result.output and "move spec.yml to .specworks/config.yml and spec/ to .specworks/" in result.output
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if ".git" not in p.relative_to(tmp_path).parts) == before
    assert not (tmp_path / ".specworks").exists() and not (tmp_path / ".claude").exists()
    assert (tmp_path / "spec.yml").read_text() == "specworks: 1\ncapabilities: {}\n"  # the old config is left as it was


# @ac AC-PROJ-002.4
def test_old_dir_key_is_rejected(project):
    cfg = project / ".specworks/config.yml"
    cfg.write_text(cfg.read_text() + "dir: spec\n")
    code, data = run_json("context")
    assert code == 1 and "'dir' is no longer a setting" in data["error"] and "always .specworks/" in data["error"]


# @ac AC-PROJ-002.3, AC-PROJ-003.1, AC-PROJ-003.2
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
        ("tests_dir: ../../outside", "'tests_dir' must be a relative folder inside the project"),
        ("tests_dir: /etc", "'tests_dir' must be a relative folder inside the project"),
        ("capabilities:\n  user-auth:\n    path: null", "capability 'user-auth' needs a 'path'"),
        ("capabilities:\n  user-auth:\n    path: src/auth\n    prefx: AUTH", "capability 'user-auth' has unknown keys: prefx"),
        ("capabilites: {}", "unknown keys: capabilites"),
    ],
)
def test_malformed_config_is_a_clear_error(project, setting, message):
    cfg = project / ".specworks/config.yml"
    key = setting.split(":", 1)[0]
    text = "\n".join(line for line in cfg.read_text().splitlines() if not line.startswith(f"{key}:"))
    cfg.write_text(f"{text}\n{setting}\n")
    code, data = run_json("context")
    assert code == 1 and message in data["error"], data


# @ac AC-PROJ-011.1
def test_phases_follow_the_workflow(project):
    run_json("new", "add-login", "--no-branch")
    code, data = run_json("status", "--change", "add-login")
    assert data["phases"] == ["refine", "specify", "design", "implement", "review", "validate", "close", "done"]
    for phase in ("implement", "specify", "close"):  # moving back is allowed; done is close's alone
        code, data = run_json("phase", phase, "--change", "add-login")
        assert code == 0 and data["phase"] == phase


# @ac AC-PROJ-011.4
@pytest.mark.parametrize("saved", ["test", "code"])
def test_a_change_saved_in_test_or_code_is_in_implement(project, saved):
    run_json("new", "add-login", "--no-branch")
    meta = project / ".specworks/changes/active/add-login/.change.yaml"
    meta.write_text(re.sub(r"(?m)^phase: .*$", f"phase: {saved}", meta.read_text(encoding="utf-8")), encoding="utf-8")
    code, data = run_json("status", "--change", "add-login")
    assert code == 0 and data["phase"] == "implement", data
    code, data = run_json("list")
    assert [c["phase"] for c in data["changes"]] == ["implement"]


# @ac AC-PROJ-011.5
@pytest.mark.parametrize("half", ["test", "code"])
def test_test_and_code_are_not_phases(project, half):
    run_json("new", "add-login", "--no-branch")
    run_json("phase", "design", "--change", "add-login")
    code, data = run_json("phase", half, "--change", "add-login")
    assert code == 1 and "implement" in data.get("error", ""), data
    assert run_json("status", "--change", "add-login")[1]["phase"] == "design"


# @ac AC-PROJ-011.3, AC-CLI-001.2
@pytest.mark.parametrize(
    "meta, message",
    [
        ("- a\n- list\n", ".specworks/changes/active/add-login/.change.yaml must be a mapping (name, created, phase), got list"),
        ("phase: [unclosed\n", "cannot read .specworks/changes/active/add-login/.change.yaml"),
        ("phase: shipping\n", "change 'add-login' has unknown phase 'shipping' in .specworks/changes/active/add-login/.change.yaml"),
    ],
    ids=["list", "bad-yaml", "unknown-phase"],
)
def test_a_broken_change_file_is_an_error_not_a_crash(project, monkeypatch, capsys, meta, message):
    run_json("new", "add-login", "--no-branch")
    (project / ".specworks/changes/active/add-login/.change.yaml").write_text(meta)
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


# @ac AC-PROJ-004.3
def test_null_description_is_empty(project):
    cfg = project / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("capabilities: {}", "capabilities:\n  user-auth:\n    path: src/auth\n    description:"))
    code, data = run_json("context")
    assert code == 0 and data["capabilities"][0]["description"] == "", data


# @ac AC-PROJ-003.5
@pytest.mark.parametrize("pad", ["true", "-1", "'24'"])
def test_diagram_pad_must_be_a_non_negative_number(project, pad):
    cfg = project / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("diagrams:\n", f"diagrams:\n  pad: {pad}\n", 1))
    code, data = run_json("context")
    assert code == 1 and "'diagrams.pad' a non-negative number" in data["error"], data


# @ac AC-PROJ-002.1, AC-PROJ-002.2, AC-PROJ-003.2, AC-PROJ-003.3, AC-PROJ-003.4, AC-PROJ-003.5
@pytest.mark.parametrize(
    "config, message",
    [
        ("specworks: 2\n", "unsupported config version specworks: 2 (expected 1)"),
        ("specworks: 1\ncontext: [\n", "cannot read"),
        ("specworks: 1\ncontext: [a, b]\n", "'context' must be a string"),
        (f"specworks: 1\ncontext: {'x' * (50 * 1024 + 1)}\n", "'context' is larger than 51200 bytes"),
        ("specworks: 1\ncommands: [uv run pytest]\n", "'commands' must be a mapping of test, test_scoped, lint, typecheck, build, format"),
        ("specworks: 1\ncommands:\n  test: [uv, run, pytest]\n", "'commands.test' must be a shell command string"),
        ("specworks: 1\nmodules: [billing]\n", "'modules' must be a mapping of name: path"),
        ("specworks: 1\ndiagrams:\n  theme: true\n", "'diagrams.theme': unknown theme True"),
        ("specworks: 1\ndiagrams:\n  dark_theme: nope\n", "or none to use the light theme in dark mode too"),
        ("specworks: 1\ntest_globs: ['tests/test_[ab].py']\n", "'test_globs': tests/test_[ab].py: globs support *, ? and ** only"),
        ("specworks: 1\nsource_globs: ['src/**/*.{ts,tsx}']\n", "'source_globs': src/**/*.{ts,tsx}: globs support *, ? and ** only"),
    ],
    ids=lambda value: value[:40],  # the test ID goes into an environment variable, which Windows caps at 32767 characters
)
def test_invalid_config_values_are_clear_errors(project, config, message):
    (project / ".specworks/config.yml").write_text(config)
    code, data = run_json("context")
    assert code == 1 and message in data["error"], data


# @ac AC-PROJ-003.6
@pytest.mark.parametrize("tools", ["claude", "{claude: true}", "[]", "[claude, cursor]", "[1]"], ids=["string", "mapping", "empty", "unknown", "number"])
def test_tools_must_be_a_list_of_known_tool_ids(project, tools):
    set_saved_tools(project, tools)
    code, data = run_json("context")
    assert code == 1 and "'tools'" in data["error"], data
    assert all(tool_id in data["error"] for tool_id in TOOL_IDS), data  # the known IDs are named


# @ac AC-PROJ-003.6
def test_a_list_of_known_tool_ids_loads(project):
    set_saved_tools(project, "[copilot, claude]")
    assert load_config(project).tools == ["copilot", "claude"]
    assert run_json("context")[0] == 0


# @ac AC-PROJ-004.1
def test_a_capability_can_be_given_as_name_and_path(project):
    (project / ".specworks/config.yml").write_text("specworks: 1\ncapabilities:\n  user-auth: src/auth/\n")
    code, data = run_json("context")
    assert code == 0 and [(c["name"], c["path"], c["prefix"]) for c in data["capabilities"]] == [("user-auth", "src/auth", "USER-AUTH")]


# @ac AC-PROJ-006.4
def test_a_broken_unrelated_outer_config_does_not_break_an_inner_project(tmp_path, monkeypatch):
    (tmp_path / ".specworks").mkdir()
    (tmp_path / ".specworks/config.yml").write_text("specworks: 1\nbogus: true\n")
    inner = tmp_path / "inner"
    inner.mkdir()
    monkeypatch.chdir(inner)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-link", "--no-skills"]).exit_code == 0
    code, data = run_json("list")
    assert code == 0 and data["changes"] == []


# @ac AC-PROJ-006.5
def test_a_broken_parent_that_links_this_module_is_still_an_error(tmp_path, monkeypatch):
    (tmp_path / ".specworks").mkdir()
    (tmp_path / ".specworks/config.yml").write_text("specworks: 1\nbogus: true\nmodules:\n  inner: inner\n")
    (tmp_path / "inner/.specworks").mkdir(parents=True)
    (tmp_path / "inner/.specworks/config.yml").write_text("specworks: 1\n")
    monkeypatch.chdir(tmp_path / "inner")
    code, data = run_json("list")
    assert code == 1 and "bogus" in data["error"]
