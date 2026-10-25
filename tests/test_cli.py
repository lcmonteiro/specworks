import json
import re

import pytest
from typer.testing import CliRunner

from helpers import git, init_repo, remove_repo
from specworks.cli import app, main
from specworks.core.git import git_text

runner = CliRunner()


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.output
    return tmp_path


@pytest.fixture
def committed(project, monkeypatch):
    """The project with everything committed on main, so a branch starts from a real commit."""
    for key, value in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(key, value)
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "baseline")
    return project


def current_branch(root):
    return git_text(root, "branch", "--show-current").strip()


def branch_names(root):
    return git_text(root, "branch", "--format=%(refname:short)").split()


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    return result.exit_code, json.loads(result.output)


# @ac AC-PROJ-001.4, AC-CLI-001.1
def test_context_without_project_reports_null_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code, data = run_json("context")
    assert code == 1
    assert data["root"] is None


# @ac AC-CLI-003.1
def test_init_creates_config_changes_and_skills(project):
    assert (project / ".specworks/config.yml").is_file()
    assert (project / ".specworks/changes/active").is_dir()
    assert (project / ".specworks/changes/archive").is_dir()
    assert (project / ".claude/skills/specworks-refine/SKILL.md").is_file()


# @ac AC-CLI-001.3
def test_init_prints_paths_relative_to_the_project_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["init", "--no-skills"])
    assert result.exit_code == 0 and result.output == "created .specworks/config.yml\nready   .specworks/changes/active/\n"


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


# @ac AC-CLI-003.7
def test_init_outside_a_git_repository_is_refused_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1 and "git init" in result.output
    assert list(tmp_path.iterdir()) == []  # no config, no folder, no skills, no repository


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


# @ac AC-CLI-006.6
def test_new_leaves_the_changes_branch_checked_out(committed):
    result = runner.invoke(app, ["new", "add-login"])
    assert result.exit_code == 0 and "add-login" in result.output
    assert current_branch(committed) == "add-login"
    git(committed, "checkout", "-q", "main")
    code, data = run_json("new", "add-refunds")
    assert code == 0 and data["branch"] == "add-refunds" and current_branch(committed) == "add-refunds"


# @ac AC-CLI-006.6
def test_a_module_change_branch_has_the_module_path(committed, monkeypatch):
    assert runner.invoke(app, ["module", "add", "services/billing"]).exit_code == 0
    monkeypatch.chdir(committed / "services/billing")
    assert runner.invoke(app, ["module", "add", "tax"]).exit_code == 0
    monkeypatch.chdir(committed)
    code, data = run_json("new", "add-invoices", "--module", "billing")
    assert code == 0 and data["branch"] == "billing/add-invoices"
    assert current_branch(committed) == "billing/add-invoices"
    git(committed, "checkout", "-q", "main")
    code, data = run_json("new", "add-vat", "--module", "billing/tax")
    assert code == 0 and data["branch"] == "billing/tax/add-vat"
    assert current_branch(committed) == "billing/tax/add-vat"


# @ac AC-CLI-006.7
def test_new_no_branch_stays_on_the_current_branch(committed):
    git(committed, "checkout", "-q", "-b", "feature")
    before = branch_names(committed)
    code, data = run_json("new", "add-login", "--no-branch")
    assert code == 0 and data["branch"] is None
    assert current_branch(committed) == "feature" and branch_names(committed) == before


# @ac AC-CLI-006.8
@pytest.mark.parametrize("extra", [[], ["--no-branch"]])
def test_new_outside_a_git_repository_creates_nothing(project, extra):
    remove_repo(project)
    code, data = run_json("new", "add-login", *extra)
    assert code == 1 and "git init" in data["error"]
    assert not (project / ".specworks/changes/active/add-login").exists()
    assert not (project / ".git").exists()


# @ac AC-CLI-006.8
def test_new_with_an_existing_branch_creates_nothing(committed):
    git(committed, "branch", "add-login")
    before = branch_names(committed)
    code, data = run_json("new", "add-login")
    assert code == 1 and "add-login" in data["error"]
    assert not (committed / ".specworks/changes/active/add-login").exists()
    assert current_branch(committed) == "main" and branch_names(committed) == before


# @ac AC-CLI-006.8
def test_new_with_a_detached_head_creates_nothing(committed):
    git(committed, "checkout", "-q", "--detach")
    before = branch_names(committed)
    code, data = run_json("new", "add-login")
    assert code == 1 and "detached" in data["error"]
    assert not (committed / ".specworks/changes/active/add-login").exists()
    assert branch_names(committed) == before and "add-login" not in branch_names(committed)


# @ac AC-CLI-006.9
def test_new_names_the_branch_it_started_from_unless_it_is_the_base(committed):
    result = runner.invoke(app, ["new", "add-refunds"])
    assert result.exit_code == 0 and "started from" not in result.output
    code, data = run_json("new", "add-vat")  # now on add-refunds
    assert code == 0 and data["startedFrom"] == "add-refunds"
    git(committed, "checkout", "-q", "main")
    code, data = run_json("new", "add-tax")
    assert code == 0 and data["startedFrom"] is None
    git(committed, "checkout", "-q", "add-refunds")
    result = runner.invoke(app, ["new", "add-login"])
    assert result.exit_code == 0 and "started from add-refunds" in result.output


# @ac AC-FLOW-002.1
def test_instructions_for_refinement(project):
    run_json("new", "add-login", "--no-branch")
    code, data = run_json("instructions", "refinement", "--change", "add-login")
    assert code == 0
    assert data["outputPath"] == ".specworks/changes/active/add-login/refinement.md"
    assert "## Options" in data["template"]
    assert data["exists"] is False


# @ac AC-FLOW-002.4
def test_instructions_for_an_unknown_artifact_are_refused(project):
    run_json("new", "add-login", "--no-branch")
    code, data = run_json("instructions", "plan", "--change", "add-login")
    assert code == 1 and "unknown artifact 'plan'" in data["error"]
    assert "refinement, proposal, specs, design, tasks, traceability, review" in data["error"]

# @ac AC-FLOW-001.2
def test_status_marks_refinement_done_once_written(project):
    run_json("new", "add-login", "--no-branch")
    (project / ".specworks/changes/active/add-login/refinement.md").write_text("# Refinement\n")
    code, data = run_json("status", "--change", "add-login")
    states = {a["id"]: a["status"] for a in data["artifacts"]}
    assert states["refinement"] == "done"


# @ac AC-CLI-004.1
def test_context_lists_capabilities_with_docs_path(project):
    (project / ".specworks/config.yml").write_text(
        "specworks: 1\ncontext: Python 3.12 service\ncapabilities:\n  user-auth:\n    path: src/auth\n"
    )
    code, data = run_json("context")
    assert code == 0
    assert data["context"] == "Python 3.12 service"
    assert data["capabilities"][0]["docsPath"] == "src/auth/docs"
    assert data["capabilities"][0]["hasSpec"] is False


# @ac AC-CLI-006.2
def test_phase_moves_and_validates(project):
    run_json("new", "add-login", "--no-branch")
    code, data = run_json("phase", "specify", "--change", "add-login")
    assert code == 0 and data["phase"] == "specify"
    code, data = run_json("phase", "shipping", "--change", "add-login")
    assert code == 1


# @ac AC-CLI-006.3
@pytest.mark.parametrize(
    "args, hint",
    [
        (["add-login", "specify"], "specworks phase specify --change add-login"),  # the order before --change
        (["specify"], "specworks phase specify --change <ref>"),
    ],
)
def test_phase_takes_the_change_like_start_and_gate(project, args, hint):
    run_json("new", "add-login", "--no-branch")
    code, data = run_json("phase", *args)
    assert code == 1 and hint in data["error"]


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
    """A project in the old layout: ``spec.yml`` with the marker and its ``spec/`` folder."""
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


# @ac AC-CLI-003.8
def test_init_has_no_dir_option(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["init", "--dir", "spec", "--no-skills"])
    assert result.exit_code == 2 and "No such option: --dir" in result.output
    assert sorted(p.name for p in tmp_path.iterdir()) == [".git"]  # no config, no folder, no skills


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


def test_nested_docs_dir_is_allowed(project):
    cfg = project / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("docs_dir: docs", "docs_dir: docs/specworks"))
    code, data = run_json("context")
    assert code == 0, data


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


# @ac AC-INTEG-005.1
def test_skills_are_installed_with_specworks_prefix(project):
    skills = sorted(p.name for p in (project / ".claude/skills").iterdir())
    assert skills and all(name.startswith("specworks-") for name in skills)
    text = (project / ".claude/skills/specworks-refine/SKILL.md").read_text()
    assert "name: specworks-refine" in text and "sw-" not in text


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


# @ac AC-CLI-002.6
def test_archived_changes_are_not_addressable(project):
    runner.invoke(app, ["new", "old", "--no-branch"])
    archived = project / ".specworks/changes/archive/2026-01-01-old"
    (project / ".specworks/changes/active/old").rename(archived)
    code, data = run_json("phase", "code", "--change", "archive/2026-01-01-old")
    assert code == 1 and "must be kebab-case" in data["error"]
    assert "phase: refine" in (archived / ".change.yaml").read_text()


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
        ("specworks: 1\ncommands: [uv run pytest]\n", "'commands' must be a mapping of test, lint, typecheck, build, format"),
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


# @ac AC-PROJ-004.1
def test_a_capability_can_be_given_as_name_and_path(project):
    (project / ".specworks/config.yml").write_text("specworks: 1\ncapabilities:\n  user-auth: src/auth/\n")
    code, data = run_json("context")
    assert code == 0 and [(c["name"], c["path"], c["prefix"]) for c in data["capabilities"]] == [("user-auth", "src/auth", "USER-AUTH")]


def test_a_yml_file_that_is_not_text_is_never_taken_for_a_config(project):
    (project / "logo.yml").write_bytes(b"\xff\xfe specworks: 1\n")  # not UTF-8: skipped, not an error
    code, data = run_json("context")
    assert code == 0 and data["root"] == str(project)


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


# @ac AC-CLI-003.5
def test_diagram_theme_on_an_existing_project_says_it_is_not_applied(project):
    result = runner.invoke(app, ["init", "--no-skills", "--diagram-theme", "c4"])
    assert result.exit_code == 0 and "--diagram-theme not applied" in result.output


def test_task_numbered_twice_is_not_ticked(project):
    run_json("new", "dup", "--no-branch")
    tasks = project / ".specworks/changes/active/dup/tasks.md"
    tasks.write_text("- [ ] 1.1 first\n- [ ] 1.1 second\n")
    code, data = run_json("task", "done", "1.1", "--change", "dup")
    assert code == 1 and "numbered more than once" in data["error"]
    assert "[x]" not in tasks.read_text()


def test_ticking_a_task_keeps_each_line_ending(project):
    run_json("new", "crlf", "--no-branch")
    tasks = project / ".specworks/changes/active/crlf/tasks.md"
    tasks.write_bytes(b"# Tasks\r\n\r\n- [ ] 1.1 first\r\n- [ ] 1.2 second\n")
    code, data = run_json("task", "done", "1.1", "--change", "crlf")
    assert code == 0, data
    assert tasks.read_bytes() == b"# Tasks\r\n\r\n- [x] 1.1 first\r\n- [ ] 1.2 second\n"
