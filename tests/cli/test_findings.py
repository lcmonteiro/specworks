"""
Writing review findings: the review.md writers and `specworks finding`.
"""

from helpers import REF, run_json, runner
from specworks.cli import app
from specworks.workflow.review import read_review
from support.findings import REVIEW, TWO_FINDINGS, change_of, read, write_review

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
