"""Build cycles: `specworks cycle` picks where the next design → test → code → review cycle starts."""

import pytest

from helpers import REF, run_json
from specworks.workflow.review import parse_review


def open_findings(text):
    return [f.to_dict() for f in parse_review(text).open]


def write_review(root, body):
    (root / "spec/changes" / REF / "review.md").write_text(f"# Review: {REF}\n\n## Findings\n\n{body}\n\n## Summary\n\nx\n")


def cycle():
    code, data = run_json("cycle", "--change", REF)
    assert code == 0, data
    return data


def test_not_reviewed_yet(project):
    data = cycle()
    assert data["reviewed"] is False and data["startAt"] is None


def test_no_open_findings_means_done(project):
    write_review(project, "- [x] R1 **code-gap** reset ignored case\n  - **Decision**: code fixed\n")
    data = cycle()
    assert data["reviewed"] and data["open"] == [] and data["startAt"] is None and data["phases"] == []


@pytest.mark.parametrize(
    "findings, start, phases",
    [
        (["code-gap"], "code", ["code", "review"]),
        (["tag", "quality"], "code", ["code", "review"]),
        (["test-gap", "code-gap"], "test", ["test", "code", "review"]),
        (["code-gap", "design-gap", "test-gap"], "design", ["design", "test", "code", "review"]),
    ],
)
def test_the_earliest_phase_wins(project, findings, start, phases):
    write_review(project, "\n".join(f"- [ ] R{i} **{kind}** something\n  - **Decision**: pending" for i, kind in enumerate(findings, 1)))
    data = cycle()
    assert data["startAt"] == start and data["phases"] == phases and data["handOver"] is None
    assert [f["type"] for f in data["open"]] == findings


def test_back_to_in_the_decision_overrides_the_type(project):
    write_review(
        project,
        "- [ ] R1 **code-gap** reset returns None\n  - **Decision**: back to design: return the token (agreed)\n"
        "- [ ] R2 **quality** no rate limit\n  - **Decision**: back to code: add a limit",
    )
    data = cycle()
    assert [f["phase"] for f in data["open"]] == ["design", "code"] and data["startAt"] == "design"


def test_a_spec_finding_hands_over_to_specify(project):
    write_review(project, "- [ ] R1 **code-gap** x\n- [ ] R2 **spec-gap** lockout also emails the user")
    data = cycle()
    assert data["startAt"] == "specify" and data["phases"] == [] and data["handOver"] == "/specworks-specify"


def test_a_spec_finding_carried_out_in_specify_resumes_the_build_at_design(project):
    # The finding stays open until review confirms it; it must not hand over to specify again.
    write_review(
        project,
        "- [ ] R1 **spec-gap** lockout also emails the user\n"
        "  - **Decision**: back to specify: add REQ-AUTH-004 for the lockout email\n"
        "  - done in specify: REQ-AUTH-004 added with AC-AUTH-004.1, task 3.1\n"
        "- [ ] R2 **code-gap** x\n  - **Decision**: back to code: y",
    )
    data = cycle()
    assert data["handOver"] is None and data["startAt"] == "design" and data["phases"] == ["design", "test", "code", "review"]
    assert data["open"][0]["doneIn"] == "specify" and "doneIn" not in data["open"][1]


@pytest.mark.parametrize("done_in, start", [("design", "test"), ("code", "review")])
def test_a_finding_done_in_a_phase_needs_the_phases_after_it(project, done_in, start):
    write_review(project, f"- [ ] R1 **design-gap** x\n  - **Decision**: back to design: y\n  - done in {done_in}: z")
    assert cycle()["startAt"] == start


def test_open_findings_parsing():
    text = (
        "## Findings\n\n- [ ] R1 **test-gap** weak assert\n  - **Decision**: back to TEST: assert the body\n"
        "- [x] R2 **design-gap** done\n  - **Decision**: back to design: was done\n"
        "- [ ] R3 untyped finding\n\n## Changed files without tags\n\n- `x.py`: back to code is not a decision here\n"
    )
    assert [f.to_dict() for f in parse_review(text).open] == [
        {"id": "R1", "type": "test-gap", "text": "**test-gap** weak assert", "phase": "test"},
        {"id": "R3", "type": "", "text": "untyped finding", "phase": "code"},
    ]


def test_back_to_on_the_finding_line_counts():
    text = "- [ ] R1 **code-gap** reset returns None. **Decision**: back to design: return the token\n"
    assert [f["phase"] for f in [f.to_dict() for f in parse_review(text).open]] == ["design"]


def test_back_to_needs_the_decision_form_and_stays_in_its_finding():
    text = (
        "- [ ] R1 **code-gap** the form goes back to design view on error\n"  # prose, no "back to <phase>:"
        "<!-- Decision: code fixed | back to specify/design/code: proposal -->\n"  # template comment
        "Back to design: a stray line outside any finding\n"
        "  - not indented under R1 any more, so it is not R1's Decision\n"
    )
    assert [f["phase"] for f in open_findings(text)] == ["code"]


def test_a_checkbox_inside_a_finding_is_part_of_it():
    text = "## Findings\n\n- [ ] R1 **code-gap** x\n  - **Decision**: back to code: y\n  - [x] sub-step done\n"
    assert [f["phase"] for f in open_findings(text)] == ["code"] and parse_review(text).problems == []


def test_a_finding_in_a_code_fence_is_an_example():
    text = (
        "## Findings\n\nNone. A finding looks like:\n\n```markdown\n- [ ] R1 **code-gap** x\n```\n\n"
        "## Changed files without tags\n\n~~~\n- `src/a.py`: config\n~~~\n"
    )
    doc = parse_review(text)
    assert doc.findings == [] and doc.problems == [] and doc.accounts_for("src/a.py")


def test_a_code_fence_under_a_finding_keeps_it_open_and_routed():
    text = "## Findings\n\n- [ ] R1 **design-gap** x\n  ```\n  - [ ] not a finding\n  ```\n  - **Decision**: back to design: y\n"
    doc = parse_review(text)
    assert [f["phase"] for f in open_findings(text)] == ["design"] and doc.problems == []


def test_finding_types_match_in_any_case_and_after_other_bold_words():
    text = "- [ ] R1 **BREAKING** **Spec-Gap** reset changes\n- [ ] R2 **spec_gap** typo\n"
    found = [(f.type, f.phase, f.routed) for f in parse_review(text).findings]
    assert found == [("spec-gap", "specify", True), ("spec_gap", "code", False)]
