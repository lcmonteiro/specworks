"""Validate phase: the final read-only report and `gate validate`."""

import hashlib
import json
import re
import sys

from helpers import REF, run_json, runner
from specworks.cli import app

FAIL = f'"{sys.executable}" -c "import sys; print(\'lint: 1 error\'); sys.exit(1)"'
PASS = f'"{sys.executable}" -c "print(\'ok\')"'


def reviewed(repo):
    (repo / "spec/changes/active" / REF / "review.md").write_text(f"# Review: {REF}\n\n## Findings\n\nNone.\n")
    run_json("phase", "review", "--change", REF)
    return repo


def set_command(root, key, command):
    cfg = root / "spec.yml"
    cfg.write_text(re.sub(rf"(?m)^  {key}:.*$", lambda _: f"  {key}: {json.dumps(command)}", cfg.read_text(), count=1))


def by_name(data):
    return {c["name"].split(" (base")[0]: c for c in data["checks"]}


def snapshot(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


# @ac AC-FLOW-013.1
def test_verify_passes_a_finished_change(repo):
    reviewed(repo)
    code, data = run_json("validate", "--change", REF, "--base", "main")
    assert code == 0, data
    assert data["verdict"] == "PASS" and data["critical"] == 0 and data["goBackTo"] == []
    assert set(data["groups"]) == {"completeness", "correctness", "coherence"}
    assert all(c["group"] in data["groups"] for c in data["checks"])
    assert by_name(data)["lint passes (commands.lint)"]["details"] == ["not configured"]


# @ac AC-FLOW-013.2
def test_verify_is_read_only(repo):
    reviewed(repo)
    before = snapshot(repo)
    run_json("validate", "--change", REF, "--base", "main")
    run_json("gate", "validate", "--change", REF, "--base", "main")
    assert snapshot(repo) == before


# @ac AC-FLOW-013.3
def test_verify_names_the_phase_to_go_back_to(repo):
    run_json("task", "undo", "1.2", "--change", REF)
    (repo / "src/auth/lockout.py").write_text("LIMIT = 3\n")
    code, data = run_json("validate", "--change", REF, "--base", "main")
    assert code == 1 and data["verdict"] == "FAIL"
    checks = by_name(data)
    assert checks["every task is done (specworks task list --pending)"]["fix"] == "/specworks-code"
    assert checks["every requirement has code (@req tag)"]["details"] == ["REQ-AUTH-002"]
    assert checks["review.md is written"]["details"] == ["write review.md (specworks instructions review)"]
    assert checks["review.md is written"]["fix"] == "/specworks-review"
    assert data["goBackTo"] == ["/specworks-code", "/specworks-review"]


# @ac AC-FLOW-013.4
def test_failing_tests_and_lint_are_critical(repo):
    reviewed(repo)
    set_command(repo, "test", FAIL)
    set_command(repo, "lint", FAIL)
    code, data = run_json("validate", "--change", REF, "--base", "main")
    checks = by_name(data)
    assert code == 1
    assert checks["the test suite passes (commands.test)"]["ok"] is False
    assert "lint: 1 error" in checks["lint passes (commands.lint)"]["details"]


# @ac AC-FLOW-003.2
def test_no_run_turns_commands_into_warnings(repo):
    reviewed(repo)
    set_command(repo, "lint", PASS)
    code, data = run_json("validate", "--change", REF, "--base", "main", "--no-run")
    assert code == 0 and data["verdict"] == "PASS" and data["warnings"] == 2


# @ac AC-FLOW-013.5
def test_outdated_diagram_fails_coherence(repo):
    reviewed(repo)
    folder = repo / "spec/changes/active" / REF / "diagrams"
    folder.mkdir()
    (folder / "flow.d2").write_text("a -> b\n")
    code, data = run_json("validate", "--change", REF, "--base", "main")
    check = by_name(data)["diagram SVGs are up to date (specworks diagrams)"]
    assert code == 1 and check["group"] == "coherence" and check["details"] == [f"spec/changes/active/{REF}/diagrams/flow.svg (missing)"]


# @ac AC-FLOW-013.6
def test_skipping_the_review_phase_is_a_warning(repo):
    (repo / "spec/changes/active" / REF / "review.md").write_text("None.\n")
    code, data = run_json("validate", "--change", REF, "--base", "main")
    phase = by_name(data)["the change went through review"]
    assert code == 0 and phase["ok"] is False and phase["blocking"] is False and phase["details"] == ["phase is refine"]


# @ac AC-FLOW-013.7
def test_gate_verify_matches_verify(repo):
    reviewed(repo)
    code, data = run_json("gate", "validate", "--change", REF, "--base", "main")
    assert code == 0 and data["passed"] is True
    (repo / "spec/changes/active" / REF / "review.md").write_text("- [ ] R1 open\n")
    code, data = run_json("gate", "validate", "--change", REF, "--base", "main")
    assert code == 1


# @ac AC-FLOW-014.5
def test_start_close_names_the_phase_that_fixes_each_failed_check(repo):
    # The close skill enters its phase with `start close`; its text output must still say where to go back.
    run_json("phase", "validate", "--change", REF)
    run_json("task", "undo", "1.2", "--change", REF)
    result = runner.invoke(app, ["start", "close", "--change", REF, "--base", "main"])
    assert result.exit_code == 1
    assert "[FAIL] every task is done (specworks task list --pending)  -> /specworks-code" in result.output
    assert "-> /specworks" not in next(line for line in result.output.splitlines() if line.startswith("[ok  ]"))
