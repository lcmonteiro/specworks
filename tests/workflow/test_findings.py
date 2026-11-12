"""Writing review findings: the review.md writers and `specworks finding`."""

import difflib

import pytest

from helpers import REF, run_json
from specworks.workflow.findings import FindingError, add_finding, close_finding, decide_finding, mark_finding_done, read_findings
from support.findings import (
    REVIEW_ARTIFACT,
    TWO_FINDINGS,
    VALIDATION_ARTIFACT,
    change_files,
    change_of,
    read,
    read_validation,
    review_path,
    validation_path,
    write_review,
    write_validation_md,
)

# The forms a refused decision is told it can take (REQ-FLOW-016), not the list of steps, which now includes review.
DECISION_FORMS = ("'back to <step>:'", "'back to design only:'", "'accepted:'")


def names_the_decision_forms(message):
    return all(form in message for form in DECISION_FORMS)


def added_lines(old, new):
    """The lines ``new`` adds to ``old``; fails if any line of ``old`` was changed or removed."""
    a, b = old.splitlines(keepends=True), new.splitlines(keepends=True)
    added = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        assert tag in ("equal", "insert"), f"{tag}: {a[i1:i2]!r} -> {b[j1:j2]!r}"
        added += b[j1:j2] if tag == "insert" else []
    return [line.rstrip("\r\n") for line in added]


def finding(root, finding_id):
    return next(f for f in read_findings(change_of(root), REVIEW_ARTIFACT).findings if f.id == finding_id)


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
    assert [(f.id, f.done) for f in read_findings(change_of(project), REVIEW_ARTIFACT).findings] == [("R1", False), ("R2", True), ("R3", False)]


# @ac AC-FLOW-016.1
def test_ac_flow_016_1_a_proposal_naming_another_step_routes_the_new_finding(project):
    write_review(project, TWO_FINDINGS)
    proposal = "back to implement: lower-case the email, with a test"
    added = add_finding(change_of(project), "code-gap", "reset ignores case in the lookup", proposal)
    assert (added.id, added.done, added.type, added.phase) == ("R3", False, "code-gap", "implement")
    again = finding(project, "R3")
    assert (again.done, again.type, again.phase) == (False, "code-gap", "implement")
    lines = added_lines(TWO_FINDINGS, read(project))
    assert f"  - **Proposal**: {proposal}" in lines
    assert [(f.id, f.done) for f in read_findings(change_of(project), REVIEW_ARTIFACT).findings] == [("R1", False), ("R2", True), ("R3", False)]


# @ac AC-FLOW-016.2
def test_ac_flow_016_2_no_review_md_creates_it_from_the_template(project):
    assert not review_path(project).exists()
    added = add_finding(change_of(project), "code-gap", "reset ignores case", "lower-case the email")
    assert added.id == "R1"
    text = read(project)
    for heading in ("## Findings", "## Changed files without tags", "## Summary"):
        assert heading in text
    assert "`<!-- path -->`" not in text  # the template's example lines are left out
    doc = read_findings(change_of(project), REVIEW_ARTIFACT)
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
            DECISION_FORMS,
        ),
        (
            lambda ch: decide_finding(ch, "R1", "back to deploy: again"),
            DECISION_FORMS,
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
    if isinstance(named, tuple):
        assert names_the_decision_forms(str(refused.value)), refused.value
    elif named is not None:
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


# @ac AC-FLOW-016.7
def test_ac_flow_016_7_a_design_only_decision_is_written_and_routed_to_design(project):
    write_review(project, f"# Review: {REF}\n\n## Findings\n\n- [ ] R1 **design-gap** the Decisions say match by prefix\n")
    before = read(project)
    decided = decide_finding(change_of(project), "R1", "back to design only: reword Decisions > Matching")
    assert (decided.phase, decided.done, decided.design_only) == ("design", False, True)
    assert added_lines(before, read(project)) == ["  - **Decision**: back to design only: reword Decisions > Matching"]
    assert finding(project, "R1").phase == "design" and finding(project, "R1").design_only is True


# @ac AC-FLOW-016.7
def test_ac_flow_016_7_only_after_another_step_is_refused(project):
    text = (
        f"# Review: {REF}\n\n## Findings\n\n"
        "- [ ] R1 **design-gap** the Decisions say match by prefix\n  - **Decision**: back to design only: reword Decisions > Matching\n"
        "- [ ] R2 **quality** x is a vague name\n"
    )
    write_review(project, text)
    with pytest.raises(FindingError) as refused:
        decide_finding(change_of(project), "R2", "back to code only: rename x")
    assert names_the_decision_forms(str(refused.value)), refused.value
    assert read(project) == text


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


# @ac AC-FLOW-016.8
def test_ac_flow_016_8_a_finding_that_quotes_a_form_routes_by_the_line_start(project):
    write_review(project, f"# Review: {REF}\n\n## Findings\n\n")
    first = add_finding(change_of(project), "quality", "list 'back to design only:' in the help", "add it after 'back to <step>:'")
    assert (first.id, first.phase, first.design_only, first.done_in) == ("R1", "code", False, "")
    second = add_finding(change_of(project), "quality", "the reader skips a quoted form", "back to test: assert 'done in code:' is read")
    assert (second.id, second.phase, second.design_only, second.done_in) == ("R2", "test", False, "")
    read_back = [(f.id, f.phase, f.design_only, f.done_in) for f in read_findings(change_of(project), REVIEW_ARTIFACT).open]
    assert read_back == [("R1", "code", False, ""), ("R2", "test", False, "")]


# --- findings in validation.md -------------------------------------------------------


# @ac AC-FLOW-016.9
def test_ac_flow_016_9_a_finding_added_to_validation(project):
    write_review(project, TWO_FINDINGS)
    change = change_of(project)
    added = add_finding(change, "code-gap", "REQ-AUTH-003 has no code", "back to code: make the check pass", artifact="validation")
    assert (added.id, added.done, added.type, added.phase) == ("V1", False, "code-gap", "code")
    text = read_validation(project)
    assert text.startswith(f"# Validation: {REF}") and "## Findings" in text and "## Summary" in text
    assert text.index("## Findings") < text.index("- [ ] V1 **code-gap** REQ-AUTH-003 has no code") < text.index("## Summary")
    doc = read_findings(change, VALIDATION_ARTIFACT)
    assert [(f.id, f.phase) for f in doc.findings] == [("V1", "code")] and doc.problems == []  # the template's example is left out
    carried = mark_finding_done(change, "V1", "code", "tagged reset.py")
    assert (carried.id, carried.done, carried.phase, carried.done_in) == ("V1", False, "review", "code")
    assert "  - done in code: tagged reset.py" in read_validation(project).splitlines()
    assert read(project) == TWO_FINDINGS


# @ac AC-FLOW-016.10
def test_ac_flow_016_10_an_unknown_check_artifact_is_refused(project):
    write_review(project, TWO_FINDINGS)
    before = change_files(project)
    with pytest.raises(FindingError) as refused:
        add_finding(change_of(project), "code-gap", "x", "back to code: y", artifact="tasks")
    assert "review" in str(refused.value) and "validation" in str(refused.value), refused.value
    assert change_files(project) == before and not validation_path(project).exists()


# @ac AC-FLOW-016.10
def test_ac_flow_016_10_an_unknown_validation_finding_is_refused(project):
    write_review(project, TWO_FINDINGS)
    write_validation_md(project, "- [ ] V1 **code-gap** x\n  - **Proposal**: back to code: y")
    before = change_files(project)
    with pytest.raises(FindingError) as refused:
        decide_finding(change_of(project), "V7", "accepted: x")
    assert "V7" in str(refused.value) and "validation.md" in str(refused.value), refused.value
    assert change_files(project) == before


OPEN_FOR_REVIEW = "- [ ] V1 **code-gap** REQ-AUTH-003 has no code\n  - **Proposal**: back to code: make the check pass\n  - done in code: tagged reset.py"


# @ac AC-FLOW-016.11
def test_ac_flow_016_11_done_in_review_routes_a_validation_finding_to_validate(project):
    write_validation_md(project, OPEN_FOR_REVIEW, "Verdict: FAIL (1 critical, 0 warnings)\n")
    before = read_validation(project)
    assert next(f for f in read_findings(change_of(project), VALIDATION_ARTIFACT).findings if f.id == "V1").phase == "review"
    carried = mark_finding_done(change_of(project), "V1", "review", "a.py accounted for")
    assert (carried.id, carried.done, carried.phase, carried.done_in) == ("V1", False, "validate", "review")
    assert added_lines(before, read_validation(project)) == ["  - done in review: a.py accounted for"]
