"""Test phase support: commands config, task ticking and the specify/test gates."""

from helpers import REF, run_json, write_tests

# --- gates ------------------------------------------------------------------


def checks(data):
    return {c["name"]: c for c in data["checks"]}


# @ac AC-FLOW-004.1
def test_propose_gate_passes_for_a_complete_plan(project):
    code, data = run_json("gate", "specify", "--change", REF)
    assert code == 0 and data["passed"] is True


# @ac AC-FLOW-004.2
def test_propose_gate_fails_without_tasks(project):
    (project / ".specworks/changes/active" / REF / "tasks.md").unlink()
    code, data = run_json("gate", "specify", "--change", REF)
    assert code == 1 and checks(data)["tasks.md is written"]["ok"] is False


# @ac AC-FLOW-007.1
def test_test_gate_lists_criteria_without_tests(project):
    write_tests(project, "AC-AUTH-003.1")
    code, data = run_json("gate", "test", "--change", REF)
    assert code == 1
    missing = checks(data)["every acceptance criterion has a test (@ac tag)"]
    assert missing["details"] == ["AC-AUTH-003.2", "AC-AUTH-002.1"]


# @ac AC-FLOW-007.1
def test_test_gate_passes_when_every_criterion_is_tested(project):
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    run_json("task", "done", "1.1", "--change", REF)  # the [test] task
    code, data = run_json("gate", "test", "--change", REF)
    assert code == 0 and data["passed"] is True


# @ac AC-FLOW-007.2
def test_test_gate_rejects_tags_to_unknown_ids(project):
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1", "AC-AUTH-003.9")
    code, data = run_json("gate", "test", "--change", REF)
    assert code == 1
    assert checks(data)["no tag refers to an unknown requirement or criterion"]["details"][0].startswith("AC-AUTH-003.9 at tests/")


# @ac AC-FLOW-007.3
def test_ac_tag_in_source_file_is_a_warning(project):
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    run_json("task", "done", "1.1", "--change", REF)
    (project / "src/auth/reset.py").write_text("# @ac AC-AUTH-003.1\n")  # specworks: ignore-tags
    code, data = run_json("gate", "test", "--change", REF)
    assert code == 0
    warn = [c for c in data["checks"] if not c["ok"]]
    assert len(warn) == 1 and warn[0]["blocking"] is False and "src/auth/reset.py:1" in warn[0]["details"][0]


def task_checks(data):
    """The gate's checks on open tasks (not `specworks check`)."""
    return [c for c in data["checks"] if "task" in c["name"] and "done" in c["name"]]


# @ac AC-FLOW-007.4
def test_test_gate_needs_the_test_tasks_done_only(project):
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    code, data = run_json("gate", "test", "--change", REF)  # 1.1 [test] and 1.2 [code] are open
    tasks = task_checks(data)
    assert code == 1 and len(tasks) == 1 and tasks[0]["blocking"] and not tasks[0]["ok"], data
    assert [d.split()[0] for d in tasks[0]["details"]] == ["1.1"]
    run_json("task", "done", "1.1", "--change", REF)
    code, data = run_json("gate", "test", "--change", REF)  # 1.2 [code] is still open
    assert code == 0 and all(c["ok"] for c in task_checks(data)), data


# @ac AC-FLOW-003.1
def test_test_gate_also_requires_valid_specs(project):
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    (project / ".specworks/changes/active" / REF / "proposal.md").unlink()
    code, data = run_json("gate", "test", "--change", REF)
    assert code == 1 and checks(data)["specs and tasks are valid (specworks check)"]["ok"] is False


# @ac AC-FLOW-003.4
def test_unknown_gate(project):
    code, data = run_json("gate", "deploy", "--change", REF)
    assert code == 1 and "no gate for phase 'deploy'" in data["error"]


# @ac AC-FLOW-004.3
def test_propose_gate_reports_a_criterion_without_a_task_once(project):
    tasks = project / ".specworks/changes/active" / REF / "tasks.md"
    tasks.write_text("\n".join(line for line in tasks.read_text().splitlines() if "AUTH-003" not in line) + "\n")
    code, data = run_json("gate", "specify", "--change", REF)
    details = [d for c in data["checks"] for d in c["details"] if "AC-AUTH-003.1" in d]
    assert code == 1 and len(details) == 1 and "is not covered by any task" in details[0]
