"""`specworks validate --write`: validate, then write validation.md and print its path."""

import re

from helpers import REF, run_json, runner
from specworks.cli import app
from specworks.workflow.findings import read_findings
from support.findings import VALIDATION, VALIDATION_ARTIFACT, change_of, read_validation, validation_path, write_review


def reviewed(repo):
    write_review(repo, f"# Review: {REF}\n\n## Findings\n\nNone.\n")
    run_json("phase", "review", "--change", REF)
    return repo


def findings_section(text):
    found = re.search(r"(?ms)^## Findings\s*$(.*?)(?=^## |\Z)", text)
    assert found, text
    return re.sub(r"(?s)<!--.*?-->", "", found.group(1)).strip()


# @ac AC-CLI-023.1
def test_ac_cli_023_1_writing_on_fail(repo):
    reviewed(repo)
    run_json("task", "undo", "1.2", "--change", REF)
    code, data = run_json("validate", "--write", "--change", REF, "--base", "main")
    assert code == 1 and data["verdict"] == "FAIL", data
    assert data["path"] == VALIDATION, data
    doc = read_findings(change_of(repo), VALIDATION_ARTIFACT)
    assert [f.phase for f in doc.open if f.type == "code-gap"] == ["code"], doc


# @ac AC-CLI-023.2
def test_ac_cli_023_2_writing_on_pass(repo):
    reviewed(repo)
    result = runner.invoke(app, ["validate", "--write", "--change", REF, "--base", "main"])
    assert result.exit_code == 0, result.output
    assert VALIDATION in result.output
    assert findings_section(read_validation(repo)) == "None."


# @ac AC-CLI-023.3
def test_ac_cli_023_3_no_write_without_the_flag(repo):
    reviewed(repo)
    run_json("task", "undo", "1.2", "--change", REF)
    code, data = run_json("validate", "--change", REF, "--base", "main")
    assert code == 1 and data["verdict"] == "FAIL", data
    assert not validation_path(repo).exists()
