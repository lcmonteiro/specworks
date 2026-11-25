"""
A change's open inspection notes by turn (REQ-FLOW-020), and inspection's `open` artifact state (REQ-FLOW-001).
"""

from helpers import run_json
from specworks.workflow.inspection import InspectionNote, inspection_turns
from support.findings import change_of, inspection_path, write_inspection
from support.reopen import make_archived

BOTH_TURNS = (
    "- [ ] I1 **code-gap** the old token is not revoked\n"
    "  - **Proposal**: back to code: revoke the old token\n"
    "- [ ] I2 **question** why a link and not a code?\n"
    "- [ ] I3 **code-gap** reset ignores case\n"
    "  - **Proposal**: back to code: lower-case the email\n"
    "  - done in code: lower-cased in reset.py\n"
    "  - done in review: the case is tested\n"
    "- [x] I4 **code-gap** the link never expires\n"
)


def statuses(ref):
    code, data = run_json("status", "--change", ref)
    assert code == 0, data
    return {a["id"]: a["status"] for a in data["artifacts"]}


# @ac AC-FLOW-020.1
def test_ac_flow_020_1_open_notes_are_split_by_turn_in_file_order(project):
    write_inspection(project, BOTH_TURNS)
    turns = inspection_turns(change_of(project))
    assert turns.author == [InspectionNote(id="I1", step="code"), InspectionNote(id="I2", step="review")]
    assert turns.reviewer == [InspectionNote(id="I3", step="inspect")]
    assert bool(turns)


# @ac AC-FLOW-020.1
def test_ac_flow_020_1_a_done_note_is_in_neither_turn(project):
    write_inspection(project, "- [x] I1 **code-gap** done\n- [ ] I2 **question** still open?\n- [x] I3 **question** answered\n")
    turns = inspection_turns(change_of(project))
    assert (turns.author, turns.reviewer) == ([InspectionNote(id="I2", step="review")], [])


# @ac AC-FLOW-020.2
def test_ac_flow_020_2_a_note_sent_back_to_specify_is_the_authors(project):
    write_inspection(project, "- [ ] I1 **question** what is the limit?\n  - **Proposal**: back to specify: add the limit\n")
    turns = inspection_turns(change_of(project))
    assert (turns.author, turns.reviewer) == ([InspectionNote(id="I1", step="specify")], [])


# @ac AC-FLOW-020.3
def test_ac_flow_020_3_notes_are_read_from_the_archive_folder(project):
    archived = make_archived(project, "xpto")
    (archived.path / "inspection.md").write_text(
        "# Inspection: xpto\n\n## Findings\n\n- [ ] I1 **code-gap** the old token is not revoked\n", encoding="utf-8"
    )
    assert not (project / ".specworks/changes/active/xpto").exists()
    turns = inspection_turns(archived)
    assert (turns.author, turns.reviewer) == ([InspectionNote(id="I1", step="code")], [])


# @ac AC-FLOW-020.4
def test_ac_flow_020_4_no_inspection_md_has_no_notes(project):
    assert not inspection_path(project).exists()
    turns = inspection_turns(change_of(project))
    assert (turns.author, turns.reviewer) == ([], []) and not turns


# @ac AC-FLOW-020.4
def test_ac_flow_020_4_done_notes_and_an_unreadable_checkbox_are_no_notes(project):
    write_inspection(project, "- [x] I1 **code-gap** done\n- [ ] the old token is not revoked\n- [ ] R2 **code-gap** another letter\n")
    turns = inspection_turns(change_of(project))
    assert (turns.author, turns.reviewer) == ([], []) and not turns


# @ac AC-FLOW-001.7
def test_ac_flow_001_7_archived_inspection_is_open_until_its_note_is_confirmed(project):
    archived = make_archived(project, "xpto")
    inspection = archived.path / "inspection.md"
    inspection.write_text("# Inspection: xpto\n\n## Findings\n\n- [ ] I1 **code-gap** x\n- [x] I2 **question** y\n", encoding="utf-8")
    assert statuses("xpto")["inspection"] == "open"
    inspection.write_text(inspection.read_text(encoding="utf-8").replace("- [ ] I1", "- [x] I1"), encoding="utf-8")
    assert statuses("xpto")["inspection"] == "done"
