import pytest

from specworks.cli import app
from support.cli import in_a_terminal, make_new_project, make_project, run_json, runner


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


def test_cli_output_is_plain_even_when_ci_forces_colour(tmp_path, monkeypatch):
    """CI's GITHUB_ACTIONS=true (or FORCE_COLOR=1) makes rich colour typer's errors, which splits text such as `--dir`."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--dir", "x"])
    assert result.exit_code == 2
    assert "\x1b" not in result.output and "No such option: --dir" in result.output


def test_nested_docs_dir_is_allowed(project):
    cfg = project / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("docs_dir: docs", "docs_dir: docs/specworks"))
    code, data = run_json("context")
    assert code == 0, data


def test_a_yml_file_that_is_not_text_is_never_taken_for_a_config(project):
    (project / "logo.yml").write_bytes(b"\xff\xfe specworks: 1\n")  # not UTF-8: skipped, not an error
    code, data = run_json("context")
    assert code == 0 and data["root"] == str(project)


@pytest.fixture
def new_project(tmp_path, monkeypatch):
    return make_new_project(tmp_path, monkeypatch)


@pytest.mark.parametrize("answer, message", [("cursor", "unknown tool 'cursor'"), (",", "no tool given")])
def test_a_bad_answer_fails_like_tools_and_writes_nothing(new_project, monkeypatch, answer, message):
    in_a_terminal(monkeypatch)
    result = runner.invoke(app, ["init"], input=f"{answer}\n")
    assert result.exit_code == 1 and message in result.output, result.output
    assert sorted(p.name for p in new_project.iterdir()) == [".git"]


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
