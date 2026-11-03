"""Test phase support: commands config, task ticking and the specify/test gates."""

from helpers import REF, run_json


# @ac AC-SPECS-009.5
def test_task_done_and_undo_only_touch_the_checkbox(project):
    path = project / ".specworks/changes/active" / REF / "tasks.md"
    before = path.read_text()
    code, data = run_json("task", "done", "1.1", "1.2", "--change", REF)
    assert code == 0 and data["done"] == 3
    after = path.read_text()
    assert after == before.replace("- [ ] 1.1", "- [x] 1.1").replace("- [ ] 1.2", "- [x] 1.2")
    run_json("task", "undo", "1.1", "1.2", "--change", REF)
    assert path.read_text() == before


# @ac AC-SPECS-009.5
def test_task_done_rejects_unknown_numbers(project):
    path = project / ".specworks/changes/active" / REF / "tasks.md"
    before = path.read_text()
    code, data = run_json("task", "done", "1.1", "9.9", "--change", REF)
    assert code == 1 and "unknown task 9.9" in data["error"]
    assert path.read_text() == before
