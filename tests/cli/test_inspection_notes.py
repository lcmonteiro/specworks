"""
Inspection notes by turn in `status` (REQ-CLI-025), `list --archived` (REQ-CLI-026) and `context`'s `inspected` (REQ-CLI-027).
"""

import pytest
from typer.testing import CliRunner

from specworks.cli import app
from support.cli import make_project, run_json
from support.modules import make_workspace
from support.reopen import DAY, make_archived

runner = CliRunner()
ARCHIVE = ".specworks/changes/archive"
FOR_THE_AUTHOR = "- [ ] I1 **code-gap** the old token is not revoked\n  - **Proposal**: back to code: revoke it\n- [ ] I2 **question** why a link?\n"
FOR_THE_REVIEWER = (
    "- [ ] I3 **code-gap** reset ignores case\n  - **Proposal**: back to code: lower-case the email\n"
    "  - done in code: lower-cased in reset.py\n  - done in review: the case is tested\n"
)


@pytest.fixture
def project(tmp_path, monkeypatch):
    """
    A project with no change, active or archived.
    """
    return make_project(tmp_path, monkeypatch)


def closed(root, name, findings=None):
    """
    Close the change ``name``; with ``findings`` (lines of Markdown), its archived inspection.md holds them.
    """
    archived = make_archived(root, name)
    if findings is not None:
        (archived.path / "inspection.md").write_text(f"# Inspection: {name}\n\n## Findings\n\n{findings}\n", encoding="utf-8")
    return archived


def abandoned(root, name, findings):
    """
    Abandon the change ``name`` with ``specworks abandon``; its archived inspection.md holds ``findings`` (lines of Markdown).
    """
    code, data = run_json("new", name, "--no-branch")
    assert code == 0, data
    code, data = run_json("abandon", "--change", name, "--reason", "not needed")
    assert code == 0, data
    (root / data["path"] / "inspection.md").write_text(f"# Inspection: {name}\n\n## Findings\n\n{findings}\n", encoding="utf-8")


def text_of(*args):
    result = runner.invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return result.output


# --- status (REQ-CLI-025) -------------------------------------------------------


# @ac AC-CLI-025.1
def test_ac_cli_025_1_status_names_the_authors_notes_and_reopen(project):
    closed(project, "xpto", FOR_THE_AUTHOR)
    code, data = run_json("status", "--change", "xpto")
    assert code == 0, data
    assert data["inspection"] == {"author": [{"id": "I1", "step": "code"}, {"id": "I2", "step": "review"}]}, data
    text = text_of("status", "--change", "xpto")
    assert "inspection notes for the author: I1, I2 → /specworks-reopen xpto" in text
    assert "inspection notes for the reviewer" not in text


# @ac AC-CLI-025.2
def test_ac_cli_025_2_status_names_the_reviewers_note_and_inspect(project):
    closed(project, "xpto", FOR_THE_REVIEWER.replace("I3", "I1"))
    code, data = run_json("status", "--change", "xpto")
    assert code == 0, data
    assert data["inspection"] == {"reviewer": [{"id": "I1", "step": "inspect"}]}, data
    text = text_of("status", "--change", "xpto")
    assert "inspection notes for the reviewer: I1 → /specworks-inspect xpto" in text
    assert "inspection notes for the author" not in text


# @ac AC-CLI-025.1, AC-CLI-025.2
def test_status_names_both_turns_of_one_change(project):
    closed(project, "xpto", FOR_THE_AUTHOR + FOR_THE_REVIEWER)
    code, data = run_json("status", "--change", "xpto")
    assert data["inspection"] == {
        "author": [{"id": "I1", "step": "code"}, {"id": "I2", "step": "review"}],
        "reviewer": [{"id": "I3", "step": "inspect"}],
    }, data
    text = text_of("status", "--change", "xpto")
    assert "inspection notes for the author: I1, I2 → /specworks-reopen xpto" in text
    assert "inspection notes for the reviewer: I3 → /specworks-inspect xpto" in text


# @ac AC-CLI-025.3
def test_ac_cli_025_3_no_open_note_or_an_active_change_has_no_inspection(project):
    closed(project, "confirmed", "- [x] I1 **code-gap** revoked\n- [x] I2 **question** answered\n")
    closed(project, "uninspected")
    code, data = run_json("new", "in-flight", "--no-branch")
    assert code == 0, data
    (project / ".specworks/changes/active/in-flight/inspection.md").write_text(f"# Inspection: in-flight\n\n## Findings\n\n{FOR_THE_AUTHOR}", encoding="utf-8")
    for ref in ("confirmed", "uninspected", "in-flight"):
        code, data = run_json("status", "--change", ref)
        assert code == 0 and "inspection" not in data, (ref, data)
        assert "inspection notes for" not in text_of("status", "--change", ref), ref


# @ac AC-CLI-025.4
def test_ac_cli_025_4_an_abandoned_change_has_no_inspection(project):
    abandoned(project, "dropped", "- [ ] I1 **code-gap** the old token is not revoked\n")
    code, data = run_json("status", "--change", "dropped")
    assert code == 0, data
    assert "inspection" not in data, data
    text = text_of("status", "--change", "dropped")
    assert "inspection notes for" not in text
    assert "/specworks-reopen" not in text


# --- list --archived (REQ-CLI-026) ----------------------------------------------


# @ac AC-CLI-026.1
def test_ac_cli_026_1_list_archived_counts_the_notes_of_each_turn(project):
    closed(project, "xpto", FOR_THE_AUTHOR + FOR_THE_REVIEWER)
    closed(project, "other")
    code, data = run_json("list", "--archived")
    assert code == 0, data
    rows = {row["ref"]: row for row in data["changes"]}
    assert rows["xpto"]["inspection"] == {
        "author": [{"id": "I1", "step": "code"}, {"id": "I2", "step": "review"}],
        "reviewer": [{"id": "I3", "step": "inspect"}],
    }, rows
    assert "inspection" not in rows["other"], rows
    lines = text_of("list", "--archived").splitlines()
    assert f"{'xpto':<32} {DAY}  closed  inspection: 2 for the author, 1 for the reviewer" in lines
    assert f"{'other':<32} {DAY}  closed" in lines


# @ac AC-CLI-026.1
def test_ac_cli_026_1_a_turn_with_no_note_is_left_out_of_the_line(project):
    closed(project, "xpto", FOR_THE_REVIEWER)
    lines = text_of("list", "--archived").splitlines()
    assert f"{'xpto':<32} {DAY}  closed  inspection: 1 for the reviewer" in lines


# @ac AC-CLI-026.2
def test_ac_cli_026_2_an_abandoned_row_has_no_inspection(project):
    abandoned(project, "dropped", "- [ ] I1 **code-gap** the old token is not revoked\n")
    code, data = run_json("list", "--archived")
    assert code == 0, data
    rows = {row["ref"]: row for row in data["changes"]}
    assert "dropped" in rows and "inspection" not in rows["dropped"], rows
    lines = [line for line in text_of("list", "--archived").splitlines() if line.startswith("dropped ")]
    assert len(lines) == 1, lines
    assert "inspection:" not in lines[0], lines


# --- context (REQ-CLI-027) ------------------------------------------------------


# @ac AC-CLI-027.1
def test_ac_cli_027_1_context_lists_an_inspected_change(project):
    archived = closed(project, "xpto", "- [ ] I1 **code-gap** the old token is not revoked\n")
    code, data = run_json("context")
    assert code == 0, data
    assert data["changes"] == []
    assert [row["ref"] for row in data["inspected"]] == ["xpto"], data["inspected"]
    row = data["inspected"][0]
    assert row["path"] == f"{ARCHIVE}/{archived.path.name}" and row["path"].startswith(f"{ARCHIVE}/{DAY}-"), row
    assert row["inspection"] == {"author": [{"id": "I1", "step": "code"}]}, row
    lines = text_of("context").splitlines()
    assert "inspected:" in lines
    assert f"  {'xpto':<24} /specworks-reopen xpto" in lines


# @ac AC-CLI-027.1
def test_ac_cli_027_1_a_change_waiting_for_the_reviewer_points_to_inspect(project):
    closed(project, "xpto", FOR_THE_REVIEWER)
    lines = text_of("context").splitlines()
    assert f"  {'xpto':<24} /specworks-inspect xpto" in lines


# @ac AC-CLI-027.2
def test_ac_cli_027_2_nothing_inspected_is_an_empty_list(project):
    closed(project, "confirmed", "- [x] I1 **code-gap** revoked\n")
    closed(project, "uninspected")
    code, data = run_json("context")
    assert code == 0 and data["inspected"] == [], data
    assert "inspected:" not in text_of("context").splitlines()


# @ac AC-CLI-027.3
def test_ac_cli_027_3_other_modules_are_listed_with_all(tmp_path, monkeypatch):
    root = make_workspace(tmp_path, monkeypatch)
    closed(root / "services/billing", "inv", "- [ ] I1 **code-gap** the total is rounded twice\n")
    code, data = run_json("context")
    assert code == 0 and data["inspected"] == [], data
    code, data = run_json("context", "--all")
    assert code == 0, data
    assert [row["ref"] for row in data["inspected"]] == ["billing:inv"], data["inspected"]
    assert data["inspected"][0]["inspection"] == {"author": [{"id": "I1", "step": "code"}]}


# @ac AC-CLI-027.4
def test_ac_cli_027_4_an_abandoned_change_is_never_inspected(project):
    abandoned(project, "dropped", "- [ ] I1 **code-gap** the old token is not revoked\n")
    closed(project, "xpto", "- [ ] I1 **code-gap** the total is rounded twice\n")
    code, data = run_json("context")
    assert code == 0, data
    assert [row["ref"] for row in data["inspected"]] == ["xpto"], data["inspected"]
    assert "dropped" not in text_of("context")
