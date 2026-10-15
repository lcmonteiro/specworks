"""Build cycles: `specworks cycle` picks where the next design → test → code → review cycle starts."""

import pytest
from helpers import REF, run_json

from specworks.workflow.cycle import open_findings


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


def test_open_findings_parsing():
    text = (
        "## Findings\n\n- [ ] R1 **test-gap** weak assert\n  - **Decision**: back to TEST: assert the body\n"
        "- [x] R2 **design-gap** done\n  - **Decision**: back to design: was done\n"
        "- [ ] R3 untyped finding\n\n## Changed files without tags\n\n- `x.py`: back to code is not a decision here\n"
    )
    assert open_findings(text) == [
        {"id": "R1", "type": "test-gap", "text": "**test-gap** weak assert", "phase": "test"},
        {"id": "R3", "type": "", "text": "untyped finding", "phase": "code"},
    ]


def test_back_to_on_the_finding_line_counts():
    text = "- [ ] R1 **code-gap** reset returns None. **Decision**: back to design: return the token\n"
    assert [f["phase"] for f in open_findings(text)] == ["design"]


def test_back_to_needs_the_decision_form_and_stays_in_its_finding():
    text = (
        "- [ ] R1 **code-gap** the form goes back to design view on error\n"  # prose, no "back to <phase>:"
        "<!-- Decision: code fixed | back to specify/design/code: proposal -->\n"  # template comment
        "Back to design: a stray line outside any finding\n"
        "  - not indented under R1 any more, so it is not R1's Decision\n"
    )
    assert [f["phase"] for f in open_findings(text)] == ["code"]
