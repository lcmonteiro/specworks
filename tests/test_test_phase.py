"""Test phase support: commands config, task ticking and the specify/test gates."""

from typer.testing import CliRunner

from helpers import REF, run_json, write_tests
from specworks.cli import app

runner = CliRunner()

# --- commands ---------------------------------------------------------------


def test_commands_are_inherited_and_overridden_by_modules(project, monkeypatch):
    cfg = project / "spec.yml"
    cfg.write_text(cfg.read_text().replace("commands:\n  test:\n  lint:\n", "commands:\n  test: uv run pytest\n  lint: ruff check .\n"))
    runner.invoke(app, ["module", "add", "web"])
    web = project / "web/spec.yml"
    web.write_text(web.read_text().replace("commands:\n  test:\n", "commands:\n  test: npm test\n"))
    code, data = run_json("context")
    assert data["commands"] == {"test": "uv run pytest", "lint": "ruff check ."}
    monkeypatch.chdir(project / "web")
    code, data = run_json("context")
    assert data["commands"] == {"test": "npm test", "lint": "ruff check ."}


def test_unknown_command_key_is_rejected(project):
    cfg = project / "spec.yml"
    cfg.write_text(cfg.read_text().replace("commands:\n  test:\n", "commands:\n  deploy: make\n  test:\n"))
    code, data = run_json("context")
    assert code == 1 and "unknown keys: deploy" in data["error"]


# --- tasks ------------------------------------------------------------------


def test_task_list(project):
    code, data = run_json("task", "list", "--change", REF)
    assert code == 0 and data["done"] == 1 and data["total"] == 3
    assert data["tasks"][0]["ids"] == ["AC-AUTH-003.1", "AC-AUTH-003.2"]
    code, data = run_json("task", "list", "--change", REF, "--pending")
    assert [t["num"] for t in data["tasks"]] == ["1.1", "1.2"]


def test_task_done_and_undo_only_touch_the_checkbox(project):
    path = project / "spec/changes" / REF / "tasks.md"
    before = path.read_text()
    code, data = run_json("task", "done", "1.1", "1.2", "--change", REF)
    assert code == 0 and data["done"] == 3
    after = path.read_text()
    assert after == before.replace("- [ ] 1.1", "- [x] 1.1").replace("- [ ] 1.2", "- [x] 1.2")
    run_json("task", "undo", "1.1", "1.2", "--change", REF)
    assert path.read_text() == before


def test_task_done_rejects_unknown_numbers(project):
    path = project / "spec/changes" / REF / "tasks.md"
    before = path.read_text()
    code, data = run_json("task", "done", "1.1", "9.9", "--change", REF)
    assert code == 1 and "unknown task 9.9" in data["error"]
    assert path.read_text() == before


def test_task_list_without_tasks_file(project):
    (project / "spec/changes" / REF / "tasks.md").unlink()
    code, data = run_json("task", "list", "--change", REF)
    assert code == 1 and "not written yet" in data["error"]


# --- gates ------------------------------------------------------------------


def checks(data):
    return {c["name"]: c for c in data["checks"]}


def test_propose_gate_passes_for_a_complete_plan(project):
    code, data = run_json("gate", "specify", "--change", REF)
    assert code == 0 and data["passed"] is True


def test_propose_gate_fails_without_tasks(project):
    (project / "spec/changes" / REF / "tasks.md").unlink()
    code, data = run_json("gate", "specify", "--change", REF)
    assert code == 1 and checks(data)["tasks.md is written"]["ok"] is False


def test_test_gate_lists_criteria_without_tests(project):
    write_tests(project, "AC-AUTH-003.1")
    code, data = run_json("gate", "test", "--change", REF)
    assert code == 1
    missing = checks(data)["every acceptance criterion has a test (@ac tag)"]
    assert missing["details"] == ["AC-AUTH-003.2", "AC-AUTH-002.1"]


def test_test_gate_passes_when_every_criterion_is_tested(project):
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    code, data = run_json("gate", "test", "--change", REF)
    assert code == 0 and data["passed"] is True


def test_test_gate_rejects_tags_to_unknown_ids(project):
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1", "AC-AUTH-003.9")
    code, data = run_json("gate", "test", "--change", REF)
    assert code == 1
    assert checks(data)["no tag refers to an unknown requirement or criterion"]["details"][0].startswith("AC-AUTH-003.9 at tests/")


def test_ac_tag_in_source_file_is_a_warning(project):
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    (project / "src/auth/reset.py").write_text("# @ac AC-AUTH-003.1\n")  # specworks: ignore-tags
    code, data = run_json("gate", "test", "--change", REF)
    assert code == 0
    warn = [c for c in data["checks"] if not c["ok"]]
    assert len(warn) == 1 and warn[0]["blocking"] is False and "src/auth/reset.py:1" in warn[0]["details"][0]


def test_test_gate_also_requires_valid_specs(project):
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    (project / "spec/changes" / REF / "proposal.md").unlink()
    code, data = run_json("gate", "test", "--change", REF)
    assert code == 1 and checks(data)["specs and tasks are valid (specworks check)"]["ok"] is False


def test_unknown_gate(project):
    code, data = run_json("gate", "deploy", "--change", REF)
    assert code == 1 and "no gate for phase 'deploy'" in data["error"]


def test_propose_gate_reports_a_criterion_without_a_task_once(project):
    tasks = project / "spec/changes" / REF / "tasks.md"
    tasks.write_text("\n".join(line for line in tasks.read_text().splitlines() if "AUTH-003" not in line) + "\n")
    code, data = run_json("gate", "specify", "--change", REF)
    details = [d for c in data["checks"] for d in c["details"] if "AC-AUTH-003.1" in d]
    assert code == 1 and len(details) == 1 and "is not covered by any task" in details[0]
