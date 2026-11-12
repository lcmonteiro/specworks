"""Check artifacts: the schema's review.md, validation.md and inspection.md, and the findings of each read with its own letter."""

import json

from helpers import REF, run_json
from specworks.workflow.artifacts import check_artifact, check_artifact_for, check_artifacts
from specworks.workflow.findings import parse_findings
from support.findings import INSPECTION_ARTIFACT, REVIEW_ARTIFACT, VALIDATION_ARTIFACT, write_inspection, write_review, write_validation_md

# --- the declared check artifacts ------------------------------------------------


# @ac AC-FLOW-018.1
def test_ac_flow_018_1_the_declared_check_artifacts():
    declared = [(a.id, a.file, a.letter, a.phase, a.blocks) for a in check_artifacts()]
    assert declared == [
        ("review", "review.md", "R", "review", ("review", "validate")),
        ("validation", "validation.md", "V", "validate", ("validate",)),
        ("inspection", "inspection.md", "I", "inspect", ()),
    ]
    assert check_artifact("validation") == VALIDATION_ARTIFACT and check_artifact("review") == REVIEW_ARTIFACT
    assert check_artifact("inspection") == INSPECTION_ARTIFACT
    assert check_artifact_for("V3") == VALIDATION_ARTIFACT and check_artifact_for("R12") == REVIEW_ARTIFACT
    assert check_artifact_for("I2") == INSPECTION_ARTIFACT


# --- reading validation.md ---------------------------------------------------------

VALIDATION_FINDINGS = (
    "## Findings\n\n"
    "- [ ] V1 **code-gap** REQ-X-001 has no code\n"
    "  - **Proposal**: back to code: make the check pass\n"
    "- [ ] V2 **quality** a.py is not accounted for\n"
    "  - **Proposal**: back to review: account for a.py\n"
)


# @ac AC-FLOW-018.2
def test_ac_flow_018_2_a_finding_in_validation_md():
    doc = parse_findings(VALIDATION_FINDINGS, VALIDATION_ARTIFACT)
    assert doc.problems == []
    assert [(f.id, f.done, f.phase) for f in doc.findings] == [("V1", False, "code"), ("V2", False, "review")]


# @ac AC-FLOW-018.3
def test_ac_flow_018_3_a_letter_from_another_artifact_is_unreadable():
    in_validation = parse_findings("## Findings\n\n- [ ] R1 **code-gap** reset ignores case\n", VALIDATION_ARTIFACT)
    assert in_validation.findings == [] and len(in_validation.problems) == 1, in_validation
    in_review = parse_findings("## Findings\n\n- [ ] V1 **code-gap** reset ignores case\n", REVIEW_ARTIFACT)
    assert in_review.findings == [] and len(in_review.problems) == 1, in_review


def checks(data):
    return {c["name"].split(" (base")[0]: c for c in data["checks"]}


def readability(data, file):
    """The readability check of the check artifact ``file``."""
    return [c for name, c in checks(data).items() if "readable" in name and file in name]


# @ac AC-FLOW-018.3
def test_ac_flow_018_3_the_gates_it_blocks_fail_on_readability(repo):
    write_review(repo, f"# Review: {REF}\n\n## Findings\n\n- [ ] V1 **code-gap** reset ignores case\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--allow-open")
    [readable] = readability(data, "review.md")
    assert code == 1 and readable["ok"] is False and readable["blocking"], data
    code, data = run_json("validate", "--change", REF, "--base", "main")
    [readable] = readability(data, "review.md")
    assert code == 1 and readable["ok"] is False and readable["fix"] == "/specworks-review", data

    write_review(repo, f"# Review: {REF}\n\n## Findings\n\nNone.\n")
    write_validation_md(repo, "- [ ] R1 **code-gap** reset ignores case")
    run_json("phase", "review", "--change", REF)
    code, data = run_json("validate", "--change", REF, "--base", "main")
    [readable] = readability(data, "validation.md")
    assert code == 1 and readable["ok"] is False and readable["blocking"] and readable["fix"] == "/specworks-validate", data
    code, data = run_json("gate", "validate", "--change", REF, "--base", "main")
    assert code == 1 and data["passed"] is False, data


# --- back to review and done in review --------------------------------------------


# @ac AC-FLOW-010.10
def test_ac_flow_010_10_back_to_review_routes_to_review():
    decided = "- [ ] R1 **code-gap** a.py has no tag\n  - **Decision**: back to review: account for a.py\n"
    doc = parse_findings(decided, REVIEW_ARTIFACT)
    assert [(f.id, f.phase, f.routed) for f in doc.open] == [("R1", "review", True)] and doc.problems == []


# @ac AC-FLOW-010.10
def test_ac_flow_010_10_back_to_review_only_is_not_a_route():
    decided = "- [ ] R1 **code-gap** a.py has no tag\n  - **Decision**: back to review only: account for a.py\n"
    (finding,) = parse_findings(decided, REVIEW_ARTIFACT).open
    assert (finding.phase, finding.design_only) == ("code", False)  # routed by its type


DONE_IN_CODE = "- [ ] V1 **code-gap** REQ-X-001 has no code\n  - **Proposal**: back to code: make the check pass\n  - done in code: tagged reset.py\n"
BACK_TO_REVIEW = "- [ ] V2 **quality** a.py is not accounted for\n  - **Proposal**: back to review: account for a.py\n"


# @ac AC-FLOW-010.11
def test_ac_flow_010_11_done_in_review_routes_on_to_validate():
    before = parse_findings("## Findings\n\n" + DONE_IN_CODE + BACK_TO_REVIEW, VALIDATION_ARTIFACT)
    assert [(f.id, f.done, f.phase) for f in before.findings] == [("V1", False, "review"), ("V2", False, "review")]
    after = parse_findings(
        "## Findings\n\n" + DONE_IN_CODE + "  - done in review: REQ-X-001 has code\n" + BACK_TO_REVIEW + "  - done in review: a.py accounted for\n",
        VALIDATION_ARTIFACT,
    )
    assert after.problems == []
    assert [(f.id, f.done, f.phase, f.done_in) for f in after.findings] == [("V1", False, "validate", "review"), ("V2", False, "validate", "review")]


# --- inspection.md ------------------------------------------------------------------


# @ac AC-FLOW-018.4
def test_ac_flow_018_4_inspection_findings_block_nothing(repo):
    write_review(repo, f"# Review: {REF}\n\n## Findings\n\nNone.\n")
    run_json("phase", "review", "--change", REF)
    code, gate = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 0 and gate["passed"] is True, gate
    code, validated = run_json("validate", "--change", REF, "--base", "main")
    assert code == 0 and validated["verdict"] == "PASS", validated

    write_inspection(repo, "- [ ] I1 **code-gap** reset ignores case\n  - **Proposal**: back to code: lower-case the email")
    code, gate_after = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 0 and gate_after["passed"] is True, gate_after
    code, validated_after = run_json("validate", "--change", REF, "--base", "main")
    assert code == 0 and validated_after["verdict"] == "PASS", validated_after
    for before, after in ((gate, gate_after), (validated, validated_after)):
        assert [c for c in after["checks"] if "I1" in json.dumps(c)] == [], after  # no check or warning about I1
        assert not_ok(after) == not_ok(before), after


def not_ok(data):
    """The checks that failed or warned, by name."""
    return sorted(c["name"].split(" (base")[0] for c in data["checks"] if not c["ok"])


# --- questions, and routing back to inspect ------------------------------------------


# @ac AC-FLOW-010.12
def test_ac_flow_010_12_a_question_is_routed_to_review():
    doc = parse_findings("## Findings\n\n- [ ] I1 **question** why is the token not returned?\n", INSPECTION_ARTIFACT)
    assert doc.problems == []
    assert [(f.id, f.done, f.type, f.phase) for f in doc.findings] == [("I1", False, "question", "review")]


CODE_GAP_I1 = "- [ ] I1 **code-gap** the old token is not revoked\n  - **Proposal**: back to code: revoke the old token\n"
CODE_GAP_V1 = CODE_GAP_I1.replace("I1", "V1")
DONE_IN_CODE_LINE = "  - done in code: revoked in reset.py\n"
DONE_IN_REVIEW_LINE = "  - done in review: revocation is tested\n"


# @ac AC-FLOW-010.13
def test_ac_flow_010_13_an_inspection_finding_comes_back_to_inspect():
    steps = []
    for lines in ("", DONE_IN_CODE_LINE, DONE_IN_CODE_LINE + DONE_IN_REVIEW_LINE):
        doc = parse_findings("## Findings\n\n" + CODE_GAP_I1 + lines, INSPECTION_ARTIFACT)
        assert doc.problems == []
        [finding] = doc.findings
        steps.append((finding.id, finding.done, finding.phase))
    assert steps == [("I1", False, "code"), ("I1", False, "review"), ("I1", False, "inspect")]


# @ac AC-FLOW-010.13
def test_ac_flow_010_13_a_validation_finding_with_the_same_lines_ends_at_validate():
    doc = parse_findings("## Findings\n\n" + CODE_GAP_V1 + DONE_IN_CODE_LINE + DONE_IN_REVIEW_LINE, VALIDATION_ARTIFACT)
    assert [(f.id, f.done, f.phase) for f in doc.findings] == [("V1", False, "validate")]
