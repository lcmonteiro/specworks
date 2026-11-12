"""Validate writes validation.md (`specworks validate --write`): a finding per failed blocking check, kept in step with the checks."""

import difflib
import re

from helpers import REF, run_json, write_tests
from specworks.cli.output import resolve_change
from specworks.core.workspace import load_workspace
from specworks.workflow.checks import GateContext
from specworks.workflow.findings import add_finding, read_findings
from specworks.workflow.validate import summary, write_validation
from support.findings import VALIDATION_ARTIFACT, read_validation, validation_path, write_review

CODE_TASKS = "every [code] task is done (specworks task list --pending)"
AC_TESTS = "every acceptance criterion has a test (@ac tag)"
ARCHITECTURE_SVG = "docs/diagrams/architecture-blocks.svg"


def reviewed(repo):
    write_review(repo, f"# Review: {REF}\n\n## Findings\n\nNone.\n")
    run_json("phase", "review", "--change", REF)
    return repo


def failing(repo):
    """An open [code] task (1.2) and a criterion with no @ac test (AC-AUTH-003.2)."""
    run_json("task", "undo", "1.2", "--change", REF)
    write_tests(repo, "AC-AUTH-003.1", "AC-AUTH-002.1")
    return repo


def write(root):
    """Run validate with the write, as `specworks validate --write` does: the checks after the write, and the path."""
    ws = load_workspace(root)
    module, change = resolve_change(ws, REF)
    return write_validation(GateContext(ws, module, change, base="main"))


def findings(root):
    ws = load_workspace(root)
    return read_findings(resolve_change(ws, REF)[1], VALIDATION_ARTIFACT)


def section(text, title):
    """The text under ``## <title>``, up to the next ``##`` heading, without HTML comments."""
    found = re.search(rf"(?ms)^## {title}\s*$(.*?)(?=^## |\Z)", text)
    assert found, text
    return re.sub(r"(?s)<!--.*?-->", "", found.group(1)).strip()


def block(text, finding_id):
    """The lines of a finding's block: its checkbox line and the indented lines under it."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if re.match(rf"- \[[ x]\] {finding_id}\b", line))
    end = start + 1
    while end < len(lines) and lines[end].startswith("  "):
        end += 1
    return lines[start:end]


# @ac AC-FLOW-019.1
def test_ac_flow_019_1_a_failed_validate_writes_a_finding_per_failed_check(repo):
    failing(reviewed(repo))
    checks, path = write(repo)
    assert path == validation_path(repo) and path.is_file()
    assert summary(checks)["verdict"] == "FAIL"
    doc = findings(repo)
    assert doc.problems == []
    assert [(f.id, f.done, f.type, f.phase, f.check) for f in doc.findings] == [
        ("V1", False, "code-gap", "code", CODE_TASKS),
        ("V2", False, "test-gap", "test", AC_TESTS),
    ]
    text = read_validation(repo)
    assert block(text, "V1")[1:] == [f"  - **Check**: {CODE_TASKS}", "  - **Proposal**: back to code: make the check pass"]
    assert block(text, "V2")[1:] == [f"  - **Check**: {AC_TESTS}", "  - **Proposal**: back to test: make the check pass"]
    assert CODE_TASKS in block(text, "V1")[0] and "1.2" in block(text, "V1")[0]
    assert AC_TESTS in block(text, "V2")[0] and "AC-AUTH-003.2" in block(text, "V2")[0]
    result = summary(checks)  # the verdict after the write: the two failed checks plus validation.md's open V1 and V2
    assert result["critical"] == 3
    verdict = section(text, "Summary").splitlines()[0]
    assert re.fullmatch(rf"Verdict: FAIL \({result['critical']} critical, {result['warnings']} warnings?\)", verdict), verdict


# @ac AC-FLOW-019.2
def test_ac_flow_019_2_a_passing_validate_writes_none_and_pass(repo):
    reviewed(repo)
    checks, path = write(repo)
    assert summary(checks)["verdict"] == "PASS"
    text = read_validation(repo)
    assert section(text, "Findings") == "None." and findings(repo).findings == []
    lines = section(text, "Summary").splitlines()
    assert re.fullmatch(r"Verdict: PASS \(0 critical, \d+ warnings?\)", lines[0]), lines
    groups = [line for line in lines if re.fullmatch(r"- (Completeness|Correctness|Coherence) \d+/\d+", line)]
    assert [line.split()[1] for line in groups] == ["Completeness", "Correctness", "Coherence"], lines


def changed_lines(old, new):
    """The (removed, added) lines from ``old`` to ``new``."""
    removed, added = [], []
    for line in difflib.ndiff(old.splitlines(), new.splitlines()):
        if line.startswith("- "):
            removed.append(line[2:])
        elif line.startswith("+ "):
            added.append(line[2:])
    return removed, added


# @ac AC-FLOW-019.3
def test_ac_flow_019_3_a_rerun_after_a_fix(repo):
    failing(reviewed(repo))
    write(repo)
    ws = load_workspace(repo)
    add_finding(resolve_change(ws, REF)[1], "quality", "the help does not name --write", "back to code: name it", artifact="validation")
    before = read_validation(repo)
    v1_before, v3_before = block(before, "V1"), block(before, "V3")
    run_json("task", "done", "1.2", "--change", REF)
    write(repo)
    after = read_validation(repo)
    doc = findings(repo)
    assert [(f.id, f.done) for f in doc.findings] == [("V1", True), ("V2", False), ("V3", False)]
    assert block(after, "V1") == [v1_before[0].replace("- [ ] V1", "- [x] V1", 1), *v1_before[1:], "  - confirmed in validate: the check passes"]
    assert block(after, "V3") == v3_before
    removed, added = changed_lines(before.split("## Summary")[0], after.split("## Summary")[0])
    assert removed == [v1_before[0]] and added == [block(after, "V1")[0], "  - confirmed in validate: the check passes"]


# @ac AC-FLOW-019.4
def test_ac_flow_019_4_warnings_stay_out_of_the_findings(repo):
    write_review(repo, f"# Review: {REF}\n\n## Findings\n\nNone.\n")  # the change stays in refine: it never reached review
    (repo / "docs/diagrams").mkdir(parents=True)
    (repo / "docs/diagrams/architecture-blocks.d2").write_text("cli -> core\n", encoding="utf-8")  # no SVG
    checks, _ = write(repo)
    assert summary(checks)["verdict"] == "PASS"
    text = read_validation(repo)
    assert section(text, "Findings") == "None."
    lines = section(text, "Summary").splitlines()
    assert lines[0].startswith("Verdict: PASS (0 critical, ")
    warnings = lines[lines.index("Warnings:") + 1 :]
    assert "- the change went through review: phase is refine" in warnings, lines
    assert any(line.startswith("- ") and ARCHITECTURE_SVG in line for line in warnings), lines


# @ac AC-FLOW-019.5
def test_ac_flow_019_5_a_check_review_fixes_is_routed_to_review(repo):
    reviewed(repo)
    (repo / "src/auth/audit.py").write_text("def audit(): ...\n")  # untagged, not accounted for in review.md
    write(repo)
    [finding] = findings(repo).findings
    assert (finding.id, finding.done, finding.type, finding.phase) == ("V1", False, "quality", "review")
    assert finding.check.startswith("changed files without tags are accounted for in review.md"), finding
    assert "src/auth/audit.py" in finding.text
    assert block(read_validation(repo), "V1")[-1] == "  - **Proposal**: back to review: make the check pass"
