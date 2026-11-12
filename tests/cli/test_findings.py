"""Writing review findings: the review.md writers and `specworks finding`."""

from helpers import REF, run_json, runner
from specworks.cli import app
from specworks.workflow.findings import read_findings
from support.findings import REVIEW, REVIEW_ARTIFACT, TWO_FINDINGS, VALIDATION, VALIDATION_ARTIFACT, change_files, change_of, read, review_path, write_review

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
    assert [(f.id, f.done) for f in read_findings(change_of(project), REVIEW_ARTIFACT).findings] == [("R1", True)]


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


# @ac AC-CLI-011.3
def test_ac_cli_011_3_a_finding_in_validation_md(project):
    code, data = run_json("finding", "add", "code-gap", "x", "--proposal", "back to code: y", "--artifact", "validation", "--change", REF)
    assert code == 0, data
    assert data["path"] == VALIDATION and (data["finding"]["id"], data["finding"]["done"], data["finding"]["phase"]) == ("V1", False, "code"), data
    code, data = run_json("finding", "close", "V1", "passes", "--change", REF)
    assert code == 0, data
    assert data["path"] == VALIDATION and (data["finding"]["id"], data["finding"]["done"]) == ("V1", True), data
    assert [(f.id, f.done) for f in read_findings(change_of(project), VALIDATION_ARTIFACT).findings] == [("V1", True)]
    assert not review_path(project).exists()


# @ac AC-CLI-011.4
def test_ac_cli_011_4_an_unknown_artifact_is_refused(project):
    write_review(project, TWO_FINDINGS)
    before = change_files(project)
    code, data = run_json("finding", "add", "code-gap", "x", "--proposal", "back to code: y", "--artifact", "tasks", "--change", REF)
    assert code == 1 and "review" in data["error"] and "validation" in data["error"], data
    assert change_files(project) == before
