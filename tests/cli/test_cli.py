import pytest

from helpers import git, init_repo, remove_repo, set_saved_tools
from specworks.cli import app
from specworks.cli import project as project_cli
from specworks.core.config import load_config
from specworks.core.git import git_text
from support.cli import in_a_terminal, make_new_project, make_project, run_json, runner


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


@pytest.fixture
def committed(project, monkeypatch):
    """
    The project with everything committed on main, so a branch starts from a real commit.
    """
    for key, value in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(key, value)
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "baseline")
    return project


def current_branch(root):
    return git_text(root, "branch", "--show-current").strip()


def branch_names(root):
    return git_text(root, "branch", "--format=%(refname:short)").split()


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


# @ac AC-CLI-003.7
def test_init_outside_a_git_repository_is_refused_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1 and "git init" in result.output
    assert list(tmp_path.iterdir()) == []  # no config, no folder, no skills, no repository


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


def stay_on_work(root):
    """
    `branch_per_change: false` at the top level, with HEAD on a branch `work`.
    """
    cfg = root / ".specworks/config.yml"
    cfg.write_text(cfg.read_text(encoding="utf-8") + "branch_per_change: false\n", encoding="utf-8")
    git(root, "checkout", "-q", "-b", "work")


# @ac AC-CLI-015.1
def test_ac_cli_015_1_the_setting_false_stays_on_the_branch(committed):
    stay_on_work(committed)
    code, data = run_json("new", "add-login")
    assert code == 0, data
    assert current_branch(committed) == "work" and "add-login" not in branch_names(committed)
    assert data["branch"] is None and data["stayedOn"] == "work"
    assert (committed / ".specworks/changes/active/add-login").is_dir()


# @ac AC-CLI-015.2
def test_ac_cli_015_2_branch_overrides_false(committed):
    stay_on_work(committed)
    result = runner.invoke(app, ["new", "add-login", "--branch"])
    assert result.exit_code == 0, result.output
    assert "add-login" in branch_names(committed) and current_branch(committed) == "add-login"
    assert "stayed on" not in result.output


# @ac AC-CLI-015.3
def test_ac_cli_015_3_no_branch_overrides_the_default(committed):
    git(committed, "checkout", "-q", "-b", "feature")
    before = branch_names(committed)
    code, data = run_json("new", "add-login", "--no-branch")
    assert code == 0, data
    assert current_branch(committed) == "feature" and branch_names(committed) == before
    assert data["branch"] is None and data["stayedOn"] == "feature"


# @ac AC-CLI-015.4
def test_ac_cli_015_4_no_setting_and_no_flag_creates_the_branch(committed):
    assert load_config(committed).branch_per_change is True
    code, data = run_json("new", "add-login")
    assert code == 0, data
    assert current_branch(committed) == "add-login" and data["branch"] == "add-login"
    assert "stayedOn" in data and data["stayedOn"] is None


# @ac AC-CLI-015.5
def test_ac_cli_015_5_the_text_output_names_the_branch_it_stayed_on(committed):
    stay_on_work(committed)
    result = runner.invoke(app, ["new", "add-login"])
    assert result.exit_code == 0, result.output
    assert "stayed on work" in result.output.splitlines()
    assert current_branch(committed) == "work"


# @ac AC-CLI-015.6
def test_ac_cli_015_6_staying_on_a_detached_head_creates_the_change(committed):
    stay_on_work(committed)
    git(committed, "checkout", "-q", "--detach")
    before = branch_names(committed)
    code, data = run_json("new", "add-login")
    assert code == 0, data
    assert (committed / ".specworks/changes/active/add-login").is_dir()
    assert current_branch(committed) == "" and branch_names(committed) == before
    assert data["branch"] is None and data["stayedOn"] is None


# @ac AC-CLI-004.1
def test_context_lists_capabilities_with_docs_path(project):
    (project / ".specworks/config.yml").write_text(
        "specworks: 1\ncontext: Python 3.12 service\ncapabilities:\n  user-auth:\n    path: src/auth\n"
    )
    code, data = run_json("context")
    assert code == 0
    assert data["context"] == "Python 3.12 service"
    assert data["capabilities"][0]["docsPath"] == "src/auth/docs"
    assert data["capabilities"][0]["testsPath"] == "tests/user-auth" and not (project / "tests/user-auth").exists()
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


# @ac AC-CLI-003.8
def test_init_has_no_dir_option(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["init", "--dir", "spec", "--no-skills"])
    assert result.exit_code == 2 and "No such option: --dir" in result.output
    assert sorted(p.name for p in tmp_path.iterdir()) == [".git"]  # no config, no folder, no skills


# @ac AC-CLI-002.6
def test_archived_changes_are_not_addressable(project):
    runner.invoke(app, ["new", "old", "--no-branch"])
    archived = project / ".specworks/changes/archive/2026-01-01-old"
    (project / ".specworks/changes/active/old").rename(archived)
    code, data = run_json("phase", "code", "--change", "archive/2026-01-01-old")
    assert code == 1 and "must be kebab-case" in data["error"]
    assert "phase: refine" in (archived / ".change.yaml").read_text()


# @ac AC-CLI-003.5
def test_diagram_theme_on_an_existing_project_says_it_is_not_applied(project):
    result = runner.invoke(app, ["init", "--no-skills", "--diagram-theme", "c4"])
    assert result.exit_code == 0 and "--diagram-theme not applied" in result.output


QUESTION = "AI tools to install skills for"


@pytest.fixture
def new_project(tmp_path, monkeypatch):
    return make_new_project(tmp_path, monkeypatch)


def skill_folders_written(root):
    return {folder for folder in (".claude/skills", ".github/skills") if (root / folder / "specworks-refine/SKILL.md").is_file()}


def saved_tools_line(root):
    return [line for line in (root / ".specworks/config.yml").read_text(encoding="utf-8").splitlines() if line.startswith("tools:")]


# @ac AC-CLI-003.9
def test_init_in_a_terminal_asks_which_tools(new_project, monkeypatch):
    (new_project / "CLAUDE.md").write_text("# Claude\n")
    in_a_terminal(monkeypatch)
    result = runner.invoke(app, ["init"], input="copilot\n")
    assert result.exit_code == 0, result.output
    question = next(line for line in result.output.splitlines() if QUESTION in line)
    assert "claude" in question and "copilot" in question and "[claude]" in question  # the detected tool is the default
    assert skill_folders_written(new_project) == {".github/skills"} and not (new_project / ".claude").exists()
    assert saved_tools_line(new_project) == ["tools: [copilot]"] and load_config(new_project).tools == ["copilot"]


# @ac AC-CLI-003.10
def test_an_empty_answer_takes_the_detected_tools(new_project, monkeypatch):
    (new_project / "CLAUDE.md").write_text("# Claude\n")
    in_a_terminal(monkeypatch)
    result = runner.invoke(app, ["init"], input="\n")
    assert result.exit_code == 0, result.output
    assert QUESTION in result.output
    assert skill_folders_written(new_project) == {".claude/skills"} and not (new_project / ".github").exists()
    assert saved_tools_line(new_project) == ["tools: [claude]"]


# @ac AC-CLI-003.11
def test_init_without_a_terminal_asks_nothing_and_saves_the_detected_tools(new_project):
    result = runner.invoke(app, ["init"])  # the runner's stdin is not a terminal, as from CI or an agent
    assert result.exit_code == 0, result.output
    assert QUESTION not in result.output
    assert skill_folders_written(new_project) == {".claude/skills"} and not (new_project / ".github").exists()
    assert saved_tools_line(new_project) == ["tools: [claude, copilot]"]


# @ac AC-CLI-003.11
def test_is_terminal_is_whether_stdin_is_a_terminal(monkeypatch):
    for tty in (True, False):
        monkeypatch.setattr("sys.stdin", type("Stdin", (), {"isatty": lambda self, tty=tty: tty})())
        assert project_cli.is_terminal() is tty


# @ac AC-CLI-003.12
def test_init_with_tools_in_a_terminal_asks_nothing(new_project, monkeypatch):
    in_a_terminal(monkeypatch)
    result = runner.invoke(app, ["init", "--tools", "copilot"])  # no input: a question would abort
    assert result.exit_code == 0, result.output
    assert QUESTION not in result.output
    assert skill_folders_written(new_project) == {".github/skills"}
    assert saved_tools_line(new_project) == ["tools: [copilot]"]


# @ac AC-CLI-003.12
def test_init_again_uses_the_saved_tools_without_asking(new_project, monkeypatch):
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    set_saved_tools(new_project, "[copilot]")
    (new_project / "CLAUDE.md").write_text("# Claude\n")  # auto would pick Claude Code
    in_a_terminal(monkeypatch)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.output
    assert QUESTION not in result.output
    assert skill_folders_written(new_project) == {".github/skills"} and not (new_project / ".claude").exists()
    assert saved_tools_line(new_project) == ["tools: [copilot]"]
