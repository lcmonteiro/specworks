"""Writing review findings: the review.md writers and `specworks finding`."""

import difflib

import pytest

from helpers import REF, run_json, runner
from specworks.cli import app
from specworks.cli.output import resolve_change
from specworks.core.workspace import load_workspace
from specworks.workflow.review import FindingError, add_finding, close_finding, decide_finding, mark_finding_done, read_review

REVIEW = f".specworks/changes/active/{REF}/review.md"
TWO_FINDINGS = (
    f"# Review: {REF}\n\n"
    "## Findings\n\n"
    "- [ ] R1 **code-gap** reset ignores case\n"
    "  - **Decision**: back to code: lower-case the email\n"
    "- [x] R2 **tag** missing tag on reset.py\n"
    "  - **Decision**: code fixed\n\n"
    "## Changed files without tags\n\n"
    "- `README.md`: docs\n"
)


def change_of(root):
    ws = load_workspace(root)
    return resolve_change(ws, REF)[1]


def review_path(root):
    return root / REVIEW


def write_review(root, text):
    review_path(root).write_text(text, encoding="utf-8")


def read(root):
    return review_path(root).read_text(encoding="utf-8")


def added_lines(old, new):
    """The lines ``new`` adds to ``old``; fails if any line of ``old`` was changed or removed."""
    a, b = old.splitlines(keepends=True), new.splitlines(keepends=True)
    added = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        assert tag in ("equal", "insert"), f"{tag}: {a[i1:i2]!r} -> {b[j1:j2]!r}"
        added += b[j1:j2] if tag == "insert" else []
    return [line.rstrip("\r\n") for line in added]


def finding(root, finding_id):
    return next(f for f in read_review(change_of(root)).findings if f.id == finding_id)


# --- the writers --------------------------------------------------------------


# @ac AC-FLOW-016.1
def test_ac_flow_016_1_a_new_finding_is_the_next_id(project):
    write_review(project, TWO_FINDINGS)
    added = add_finding(change_of(project), "test-gap", "AC-AUTH-003.2 only checks the status", "assert the error message too")
    assert (added.id, added.done, added.type, added.phase) == ("R3", False, "test-gap", "test")
    again = finding(project, "R3")
    assert (again.done, again.type, again.phase) == (False, "test-gap", "test")
    lines = added_lines(TWO_FINDINGS, read(project))
    assert "  - **Proposal**: assert the error message too" in lines
    assert any(line.lstrip().startswith("- [ ] R3") and "**test-gap**" in line for line in lines)
    assert [(f.id, f.done) for f in read_review(change_of(project)).findings] == [("R1", False), ("R2", True), ("R3", False)]


# @ac AC-FLOW-016.2
def test_ac_flow_016_2_no_review_md_creates_it_from_the_template(project):
    assert not review_path(project).exists()
    added = add_finding(change_of(project), "code-gap", "reset ignores case", "lower-case the email")
    assert added.id == "R1"
    text = read(project)
    for heading in ("## Findings", "## Changed files without tags", "## Summary"):
        assert heading in text
    assert "`<!-- path -->`" not in text  # the template's example lines are left out
    doc = read_review(change_of(project))
    assert [(f.id, f.type, f.done) for f in doc.findings] == [("R1", "code-gap", False)] and doc.problems == []
    assert "  - **Proposal**: lower-case the email" in text.splitlines()
    assert text.index("## Findings") < text.index("- [ ] R1") < text.index("## Changed files without tags")


# @ac AC-FLOW-016.3
def test_ac_flow_016_3_a_decision_routes_then_is_replaced(project):
    write_review(project, f"# Review: {REF}\n\n## Findings\n\n- [ ] R1 **quality** reset() is 80 lines long\n")
    change = change_of(project)
    routed = decide_finding(change, "R1", "back to design: return the token")
    assert (routed.phase, routed.done) == ("design", False)
    assert "  - **Decision**: back to design: return the token" in read(project).splitlines()
    accepted = decide_finding(change, "R1", "accepted: rare enough")
    assert accepted.done is True
    decisions = [line for line in read(project).splitlines() if "**Decision**:" in line]
    assert decisions == ["  - **Decision**: accepted: rare enough"]
    assert finding(project, "R1").done is True
    assert read(project).splitlines()[4].startswith("- [x] R1 **quality**")


# @ac AC-FLOW-016.4
def test_ac_flow_016_4_done_in_a_step_then_confirmed(repo):
    write_review(repo, f"# Review: {REF}\n\n## Findings\n\n- [ ] R1 **code-gap** lockout also logs\n  - **Decision**: back to specify: add AC-X-001.2\n")
    change = change_of(repo)
    carried = mark_finding_done(change, "R1", "specify", "added AC-X-001.2")
    assert (carried.phase, carried.done, carried.done_in) == ("design", False, "specify")
    assert "  - done in specify: added AC-X-001.2" in read(repo).splitlines()
    closed = close_finding(change, "R1", "AC-X-001.2 is in the delta spec")
    assert closed.done is True and finding(repo, "R1").done is True
    assert "  - confirmed in review: AC-X-001.2 is in the delta spec" in read(repo).splitlines()
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    no_open = {c["name"]: c for c in data["checks"]}["no open finding in review.md"]
    assert no_open["ok"] is True, no_open


# @ac AC-FLOW-016.5
@pytest.mark.parametrize(
    "write, named",
    [
        (lambda ch: add_finding(ch, "nope-gap", "something", "a proposal"), "nope-gap"),
        (lambda ch: add_finding(ch, "code-gap", "", "a proposal"), None),
        (lambda ch: add_finding(ch, "code-gap", "something", ""), None),
        (
            lambda ch: decide_finding(ch, "R1", "fix it later"),
            "a decision starts with 'back to <step>:' (specify, design, implement, test or code) or 'accepted:'",
        ),
        (
            lambda ch: decide_finding(ch, "R1", "back to review: again"),
            "a decision starts with 'back to <step>:' (specify, design, implement, test or code) or 'accepted:'",
        ),
        (lambda ch: mark_finding_done(ch, "R1", "deploy", "shipped it"), "deploy"),
        (lambda ch: mark_finding_done(ch, "R1", "code", ""), None),
        (lambda ch: close_finding(ch, "R1", " "), None),
        (lambda ch: decide_finding(ch, "R9", "accepted: x"), "no finding R9 in "),
        (lambda ch: mark_finding_done(ch, "R9", "code", "x"), "no finding R9 in "),
        (lambda ch: close_finding(ch, "R9", "x"), "no finding R9 in "),
    ],
)
def test_ac_flow_016_5_refusals_leave_review_md_unchanged(project, write, named):
    write_review(project, TWO_FINDINGS)
    with pytest.raises(FindingError) as refused:
        write(change_of(project))
    if named is not None:
        assert named in str(refused.value)
    assert read(project) == TWO_FINDINGS


# @ac AC-FLOW-016.5
def test_ac_flow_016_5_unknown_finding_names_review_md(project):
    write_review(project, TWO_FINDINGS)
    with pytest.raises(FindingError) as refused:
        decide_finding(change_of(project), "R9", "accepted: x")
    assert str(refused.value).startswith("no finding R9 in ") and str(refused.value).rstrip().endswith("review.md")
    assert read(project) == TWO_FINDINGS


# @ac AC-FLOW-016.5
def test_ac_flow_016_5_no_review_md_for_an_existing_id(project):
    with pytest.raises(FindingError) as refused:
        close_finding(change_of(project), "R1", "x")
    assert "no finding R1 in " in str(refused.value)
    assert not review_path(project).exists()


HAND_WRITTEN = (
    f"# Review: {REF}\n\n"
    "<!-- written by hand -->\n"
    "## Findings\n\n"
    "<!-- guidance\nover two lines -->\n\n"
    "* [ ] **R1** **code-gap** reset ignores case (`src/auth/reset.py:3`)\n"
    "  Free text under the finding.\n"
    "  <!-- a note in the block -->\n\n"
    "A paragraph after it.\n\n"
    "## Summary\n\n"
    "Nothing else.  \n"
)


# @ac AC-FLOW-016.6
def test_ac_flow_016_6_other_text_is_kept_byte_for_byte(project):
    write_review(project, HAND_WRITTEN)
    decided = decide_finding(change_of(project), "R1", "back to code: lower-case the email")
    assert decided.phase == "code" and decided.done is False
    assert added_lines(HAND_WRITTEN, read(project)) == ["  - **Decision**: back to code: lower-case the email"]
    assert "<!-- a note in the block -->" in read(project) and "<!-- guidance\nover two lines -->" in read(project)


# --- specworks finding ---------------------------------------------------------


# @ac AC-CLI-011.1
def test_ac_cli_011_1_the_four_commands(project):
    steps = [
        (["finding", "add", "test-gap", "AC-AUTH-003.2 only checks the status", "--proposal", "assert the message"], "test", False),
        (["finding", "decide", "R1", "back to design: return the token"], "design", False),
        (["finding", "done", "R1", "returned ResetToken", "--in", "design"], "implement", False),
        (["finding", "close", "R1", "the token is returned and tested"], "implement", True),
    ]
    for args, phase, done in steps:
        code, data = run_json(*args, "--change", REF)
        assert code == 0, data
        assert data["path"] == REVIEW
        got = data["finding"]
        assert got["id"] == "R1" and got["done"] is done, got
        assert got["phase"] == phase, got
    assert data["finding"]["doneIn"] == "design"
    assert [(f.id, f.done) for f in read_review(change_of(project)).findings] == [("R1", True)]


# @ac AC-CLI-011.1
def test_ac_cli_011_1_text_output(project):
    result = runner.invoke(app, ["finding", "add", "code-gap", "reset ignores case", "--proposal", "lower-case it", "--change", REF])
    assert result.exit_code == 0, result.output
    assert "R1 code-gap -> code (open)" in result.output and REVIEW in result.output


# @ac AC-CLI-011.2
def test_ac_cli_011_2_a_refusal_is_an_error(project):
    write_review(project, TWO_FINDINGS)
    code, data = run_json("finding", "decide", "R9", "accepted: x", "--change", REF)
    assert code == 1 and "R9" in data["error"], data
    assert read(project) == TWO_FINDINGS
