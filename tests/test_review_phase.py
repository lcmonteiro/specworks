"""Review phase support: drift candidates (`specworks review`) and the review gate."""

from helpers import REF, run_json

def findings(data):
    return data["findings"]


def test_review_without_drift(repo):
    code, data = run_json("review", "--change", REF, "--base", "main")
    assert code == 0 and data["base"] == "main"
    assert data["findingCount"] == 0, findings(data)
    kinds = {f["path"]: f["kind"] for f in data["changedFiles"]}
    assert kinds["src/auth/reset.py"] == "source" and kinds["tests/test_reset.py"] == "test"
    assert not any(p.startswith("spec/") for p in kinds)  # workflow files are not code


def test_review_finds_untagged_code_and_tests(repo):
    (repo / "src/auth/audit.py").write_text("def audit(): ...\n")  # untracked, no tag
    (repo / "src/auth/session.py").write_text("def session(): return 1\n")  # modified, no tag
    (repo / "tests/test_audit.py").write_text("def test_audit(): ...\n")
    (repo / "README.md").write_text("docs\n")  # not code: listed, not a finding
    code, data = run_json("review", "--change", REF, "--base", "main")
    assert findings(data)["untracedSource"] == ["src/auth/audit.py", "src/auth/session.py"]
    assert findings(data)["untracedTests"] == ["tests/test_audit.py"]
    assert {"path": "README.md", "kind": "other", "tags": []} in data["changedFiles"]


def test_review_finds_spec_side_gaps(repo):
    (repo / "src/auth/lockout.py").write_text("LIMIT = 3\n")
    (repo / "tests/test_reset.py").write_text("# @ac AC-AUTH-003.1\n# @ac AC-AUTH-003.7\n")
    code, data = run_json("review", "--change", REF, "--base", "main")
    f = findings(data)
    assert f["reqWithoutCode"] == ["REQ-AUTH-002"]
    assert f["acWithoutTests"] == ["AC-AUTH-003.2", "AC-AUTH-002.1"]
    assert f["unknownTags"] == ["AC-AUTH-003.7 at tests/test_reset.py:2"]
    assert f["untracedSource"] == ["src/auth/lockout.py"]


def test_review_without_git_checks_only_the_spec_side(project):
    code, data = run_json("review", "--change", REF)
    assert code == 0 and data["changedFiles"] is None and "changed files unknown" in data["note"]


def test_review_unknown_base(repo):
    code, data = run_json("review", "--change", REF, "--base", "nope")
    assert data["changedFiles"] is None and "nope" in data["note"]


# --- gate review ------------------------------------------------------------


def checks(data):
    return {c["name"].split(" (base")[0]: c for c in data["checks"]}


def write_review(repo, body):
    (repo / "spec/changes" / REF / "review.md").write_text(f"# Review: {REF}\n\n## Findings\n\n{body}\n")


def test_gate_review_needs_review_md(repo):
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 1 and checks(data)["review.md is written"]["ok"] is False


def test_gate_review_blocks_on_open_findings(repo):
    write_review(repo, "- [ ] R1 **spec-gap** lockout also logs\n  - **Decision**: pending\n- [x] R2 **tag** fixed\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 1 and checks(data)["no open finding in review.md"]["details"] == ["R1 **spec-gap** lockout also logs"]


def test_gate_review_requires_untagged_files_accounted_for(repo):
    (repo / "src/auth/audit.py").write_text("def audit(): ...\n")
    write_review(repo, "None.\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 1
    assert checks(data)["changed files without tags are accounted for in review.md"]["details"] == ["src/auth/audit.py"]
    write_review(repo, "None.\n\n## Changed files without tags\n\n- `src/auth/audit.py`: logging helper, no behaviour\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 0 and data["passed"] is True


def test_gate_review_passes_when_clean(repo):
    write_review(repo, "- [x] R1 **test-gap** AC-AUTH-003.2 only checked the status\n  - **Decision**: code fixed\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 0, data


def test_review_artifact_has_instructions(repo):
    code, data = run_json("instructions", "review", "--change", REF)
    assert data["outputPath"] == f"spec/changes/{REF}/review.md"
    assert "## Changed files without tags" in data["template"] and "spec-gap" in data["instruction"]
