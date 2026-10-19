import json

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


# @ac AC-PROJ-001.4
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


# @ac AC-PROJ-010.1
def test_new_change_starts_in_refine_phase(project):
    code, data = run_json("new", "add-login")
    assert code == 0
    assert data["phase"] == "refine"
    code, data = run_json("list")
    assert [c["name"] for c in data["changes"]] == ["add-login"]


# @ac AC-PROJ-010.2
@pytest.mark.parametrize("name", ["Add_Login", "add login", "x--y", "archive-"])
def test_new_rejects_non_kebab_names(project, name):
    code, data = run_json("new", name)
    assert code == 1
    assert "kebab-case" in data["error"]


# @ac AC-PROJ-010.3
def test_new_rejects_duplicates(project):
    run_json("new", "add-login")
    code, data = run_json("new", "add-login")
    assert code == 1 and "already exists" in data["error"]


# @ac AC-FLOW-002.1
def test_instructions_for_refinement(project):
    run_json("new", "add-login")
    code, data = run_json("instructions", "refinement", "--change", "add-login")
    assert code == 0
    assert data["outputPath"] == "specworks/changes/add-login/refinement.md"
    assert "## Options" in data["template"]
    assert data["exists"] is False


# @ac AC-FLOW-002.4
def test_instructions_for_an_unknown_artifact_are_refused(project):
    run_json("new", "add-login")
    code, data = run_json("instructions", "plan", "--change", "add-login")
    assert code == 1 and "unknown artifact 'plan'" in data["error"]
    assert "refinement, proposal, specs, design, tasks, traceability, review" in data["error"]

# @ac AC-FLOW-001.2
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
    code, data = run_json("phase", "specify", "--change", "add-login")
    assert code == 0 and data["phase"] == "specify"
    code, data = run_json("phase", "shipping", "--change", "add-login")
    assert code == 1


@pytest.mark.parametrize(
    "args, hint",
    [
        (["add-login", "specify"], "specworks phase specify --change add-login"),  # the order before --change
        (["specify"], "specworks phase specify --change <ref>"),
    ],
)
def test_phase_takes_the_change_like_start_and_gate(project, args, hint):
    run_json("new", "add-login")
    code, data = run_json("phase", *args)
    assert code == 1 and hint in data["error"]


# @ac AC-PROJ-011.2
def test_only_close_makes_a_change_done(project):
    run_json("new", "add-login")
    code, data = run_json("phase", "done", "--change", "add-login")
    assert code == 1 and "only through `specworks close`" in data["error"]
    code, data = run_json("list")
    assert [c["phase"] for c in data["changes"]] == ["refine"]


# @ac AC-PROJ-001.1, AC-PROJ-009.1
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


# @ac AC-PROJ-001.1
def test_renaming_config_renames_folder(project):
    (project / "specworks.yml").rename(project / "context.yml")
    code, data = run_json("new", "add-login")
    assert data["path"] == "context/changes/add-login"


# @ac AC-PROJ-001.2
def test_unrelated_yml_is_not_a_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs.yml").write_text("site_name: my docs\n")
    code, data = run_json("context")
    assert code == 1 and data["root"] is None


# @ac AC-PROJ-001.3
def test_two_configs_in_one_folder_is_an_error(project):
    (project / "spec.yml").write_text("specworks: 1\n")
    code, data = run_json("context")
    assert code == 1 and "several specworks configs" in data["error"]


# @ac AC-PROJ-002.4
def test_old_dir_key_is_rejected(project):
    cfg = project / "specworks.yml"
    cfg.write_text(cfg.read_text() + "dir: spec\n")
    code, data = run_json("context")
    assert code == 1 and "'dir' is no longer a setting" in data["error"]


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


# @ac AC-PROJ-009.2
@pytest.mark.parametrize("folder", ["/abs", "../outside", ".", "", "docs/spec", ".hidden"])
def test_init_rejects_bad_dir(tmp_path, monkeypatch, folder):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--dir", folder])
    assert result.exit_code == 1
    assert list(tmp_path.glob("*.yml")) == []


# @ac AC-PROJ-011.1
def test_phases_follow_the_workflow(project):
    run_json("new", "add-login")
    code, data = run_json("status", "--change", "add-login")
    assert data["phases"] == ["refine", "specify", "design", "test", "code", "review", "validate", "close", "done"]
    for phase in ("code", "specify", "close"):  # moving back is allowed; done is close's alone
        code, data = run_json("phase", phase, "--change", "add-login")
        assert code == 0 and data["phase"] == phase


# @ac AC-INTEG-005.1
def test_skills_are_installed_with_specworks_prefix(project):
    skills = sorted(p.name for p in (project / ".claude/skills").iterdir())
    assert skills and all(name.startswith("specworks-") for name in skills)
    text = (project / ".claude/skills/specworks-refine/SKILL.md").read_text()
    assert "name: specworks-refine" in text and "sw-" not in text


# @ac AC-PROJ-011.3
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


# @ac AC-PROJ-004.3
def test_null_description_is_empty(project):
    cfg = project / "specworks.yml"
    cfg.write_text(cfg.read_text().replace("capabilities: {}", "capabilities:\n  user-auth:\n    path: src/auth\n    description:"))
    code, data = run_json("context")
    assert code == 0 and data["capabilities"][0]["description"] == "", data


def test_archived_changes_are_not_addressable(project):
    runner.invoke(app, ["new", "old"])
    archived = project / "specworks/changes/archive/2026-01-01-old"
    (project / "specworks/changes/old").rename(archived)
    code, data = run_json("phase", "code", "--change", "archive/2026-01-01-old")
    assert code == 1 and "must be kebab-case" in data["error"]
    assert "phase: refine" in (archived / ".change.yaml").read_text()


# @ac AC-PROJ-003.5
@pytest.mark.parametrize("pad", ["true", "-1", "'24'"])
def test_diagram_pad_must_be_a_non_negative_number(project, pad):
    cfg = project / "specworks.yml"
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
    (project / "specworks.yml").write_text(config)
    code, data = run_json("context")
    assert code == 1 and message in data["error"], data


# @ac AC-PROJ-004.1
def test_a_capability_can_be_given_as_name_and_path(project):
    (project / "specworks.yml").write_text("specworks: 1\ncapabilities:\n  user-auth: src/auth/\n")
    code, data = run_json("context")
    assert code == 0 and [(c["name"], c["path"], c["prefix"]) for c in data["capabilities"]] == [("user-auth", "src/auth", "USER-AUTH")]


# @ac AC-PROJ-001.2
def test_a_yml_file_that_is_not_text_is_never_taken_for_a_config(project):
    (project / "logo.yml").write_bytes(b"\xff\xfe specworks: 1\n")  # not UTF-8: skipped, not an error
    code, data = run_json("context")
    assert code == 0 and data["root"] == str(project)


# @ac AC-PROJ-006.4
def test_a_broken_unrelated_outer_config_does_not_break_an_inner_project(tmp_path, monkeypatch):
    (tmp_path / "spec.yml").write_text("specworks: 1\nbogus: true\n")
    inner = tmp_path / "inner"
    inner.mkdir()
    monkeypatch.chdir(inner)
    assert runner.invoke(app, ["init", "--no-link", "--no-skills"]).exit_code == 0
    code, data = run_json("list")
    assert code == 0 and data["changes"] == []


# @ac AC-PROJ-006.5
def test_a_broken_parent_that_links_this_module_is_still_an_error(tmp_path, monkeypatch):
    (tmp_path / "spec.yml").write_text("specworks: 1\nbogus: true\nmodules:\n  inner: inner\n")
    (tmp_path / "inner").mkdir()
    (tmp_path / "inner/spec.yml").write_text("specworks: 1\n")
    monkeypatch.chdir(tmp_path / "inner")
    code, data = run_json("list")
    assert code == 1 and "bogus" in data["error"]


def test_diagram_theme_on_an_existing_project_says_it_is_not_applied(project):
    result = runner.invoke(app, ["init", "--no-skills", "--diagram-theme", "c4"])
    assert result.exit_code == 0 and "--diagram-theme not applied" in result.output


def test_task_numbered_twice_is_not_ticked(project):
    run_json("new", "dup")
    tasks = project / "specworks/changes/dup/tasks.md"
    tasks.write_text("- [ ] 1.1 first\n- [ ] 1.1 second\n")
    code, data = run_json("task", "done", "1.1", "--change", "dup")
    assert code == 1 and "numbered more than once" in data["error"]
    assert "[x]" not in tasks.read_text()


def test_ticking_a_task_keeps_each_line_ending(project):
    run_json("new", "crlf")
    tasks = project / "specworks/changes/crlf/tasks.md"
    tasks.write_bytes(b"# Tasks\r\n\r\n- [ ] 1.1 first\r\n- [ ] 1.2 second\n")
    code, data = run_json("task", "done", "1.1", "--change", "crlf")
    assert code == 0, data
    assert tasks.read_bytes() == b"# Tasks\r\n\r\n- [x] 1.1 first\r\n- [ ] 1.2 second\n"
