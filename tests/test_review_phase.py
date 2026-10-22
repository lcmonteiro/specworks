"""Review phase support: drift candidates (`specworks review`) and the review gate."""

import json
import re
import sys

import pytest

from helpers import REF, git, remove_repo, run_json, write_tests

FAIL = f'"{sys.executable}" -c "import sys; print(\'2 failed\'); sys.exit(3)"'


def findings(data):
    return data["findings"]


# @ac AC-FLOW-009.1
def test_review_without_drift(repo):
    code, data = run_json("review", "--change", REF, "--base", "main")
    assert code == 0 and data["base"] == "main"
    assert data["findingCount"] == 0, findings(data)
    kinds = {f["path"]: f["kind"] for f in data["changedFiles"]}
    assert kinds["src/auth/reset.py"] == "source" and kinds["tests/test_reset.py"] == "test"
    assert not any(p.startswith("spec/") for p in kinds)  # workflow files are not code


# @ac AC-FLOW-009.2
def test_review_finds_untagged_code_and_tests(repo):
    (repo / "src/auth/audit.py").write_text("def audit(): ...\n")  # untracked, no tag
    (repo / "src/auth/session.py").write_text("def session(): return 1\n")  # modified, no tag
    (repo / "tests/test_audit.py").write_text("def test_audit(): ...\n")
    (repo / "README.md").write_text("docs\n")  # not code: listed, not a finding
    code, data = run_json("review", "--change", REF, "--base", "main")
    assert findings(data)["untracedSource"] == ["src/auth/audit.py", "src/auth/session.py"]
    assert findings(data)["untracedTests"] == ["tests/test_audit.py"]
    assert {"path": "README.md", "kind": "other", "tags": []} in data["changedFiles"]


# @ac AC-FLOW-009.3
def test_review_finds_spec_side_gaps(repo):
    (repo / "src/auth/lockout.py").write_text("LIMIT = 3\n")
    (repo / "tests/test_reset.py").write_text("# @ac AC-AUTH-003.1\n# @ac AC-AUTH-003.7\n")  # specworks: ignore-tags
    code, data = run_json("review", "--change", REF, "--base", "main")
    f = findings(data)
    assert f["reqWithoutCode"] == ["REQ-AUTH-002"]
    assert f["acWithoutTests"] == ["AC-AUTH-003.2", "AC-AUTH-002.1"]
    assert f["unknownTags"] == ["AC-AUTH-003.7 at tests/test_reset.py:2"]
    assert f["untracedSource"] == ["src/auth/lockout.py"]


# @ac AC-FLOW-009.4
def test_review_without_git_checks_only_the_spec_side(project):
    remove_repo(project)
    code, data = run_json("review", "--change", REF)
    assert code == 0 and data["changedFiles"] is None and "changed files unknown" in data["note"]


# @ac AC-FLOW-009.4
def test_review_unknown_base(repo):
    code, data = run_json("review", "--change", REF, "--base", "nope")
    assert data["changedFiles"] is None and "nope" in data["note"]


# @ac AC-FLOW-009.4
def test_review_finds_a_local_main_when_origin_has_no_head(repo):
    # The repo has no remote, so origin/HEAD and origin/main are missing: the local main is the base.
    code, data = run_json("review", "--change", REF)
    assert data["base"] == "main" and data["changedFiles"] is not None


# @ac AC-FLOW-009.4
def test_review_without_any_base_branch_says_to_pass_one(repo):
    git(repo, "branch", "-m", "main", "trunk")
    code, data = run_json("review", "--change", REF)
    assert data["changedFiles"] is None and "pass --base <branch>" in data["note"]


# --- gate review ------------------------------------------------------------


def checks(data):
    return {c["name"].split(" (base")[0]: c for c in data["checks"]}


def write_review(repo, body):
    (repo / "spec/changes" / REF / "review.md").write_text(f"# Review: {REF}\n\n## Findings\n\n{body}\n")


# @ac AC-FLOW-011.1
def test_gate_review_needs_review_md(repo):
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 1 and checks(data)["review.md is written"]["ok"] is False


# @ac AC-FLOW-011.1
def test_gate_review_blocks_on_open_findings(repo):
    write_review(repo, "- [ ] R1 **spec-gap** lockout also logs\n  - **Decision**: pending\n- [x] R2 **tag** fixed\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 1 and checks(data)["no open finding in review.md"]["details"] == ["R1 **spec-gap** lockout also logs"]


# @ac AC-FLOW-010.1
@pytest.mark.parametrize("line", ["* [ ] R1 **code-gap** reset ignores case", "- [ ] **R1** **code-gap** reset ignores case", "1. [ ] R1 **code-gap** x"])
def test_gate_review_reads_common_finding_variants(repo, line):
    write_review(repo, line + "\n  - **Decision**: pending\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 1 and checks(data)["no open finding in review.md"]["details"][0].startswith("R1 ")


# @ac AC-FLOW-010.2
def test_an_unreadable_finding_blocks_review_and_validate(repo):
    # Silently skipping it would let the gate pass with the finding open, even inside a build.
    write_review(repo, "- [ ] **R1 code-gap** reset ignores case\n  - **Decision**: pending\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--allow-open")
    readable = checks(data)["every finding in review.md is readable (- [ ] R<n> ...)"]
    assert code == 1 and readable["blocking"] and "is not a finding" in readable["details"][0]
    code, data = run_json("validate", "--change", REF, "--base", "main")
    readable = {c["name"]: c for c in data["checks"]}["every finding in review.md is readable (- [ ] R<n> ...)"]
    assert code == 1 and not readable["ok"] and readable["fix"] == "/specworks-review"
    assert any("is not a finding" in d for d in readable["details"])


# @ac AC-FLOW-011.2
def test_gate_review_allow_open_reports_open_findings_as_a_warning(repo):
    # Inside /specworks-build, open findings start the next cycle instead of failing the review.
    write_review(repo, "- [ ] R1 **design-gap** reset returns None\n  - **Decision**: back to design: return the token\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--allow-open")
    open_check = checks(data)["no open finding in review.md"]
    assert code == 0 and open_check["ok"] is False and open_check["blocking"] is False
    (repo / "src/auth/audit.py").write_text("def audit(): ...\n")  # everything else still blocks
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--allow-open")
    assert code == 1


def fail_the_suite(repo):
    cfg = repo / "spec.yml"
    cfg.write_text(re.sub(r"(?m)^  test:.*$", lambda _: f"  test: {json.dumps(FAIL)}", cfg.read_text(), count=1))


TESTS = "the test suite passes (commands.test)"


# @ac AC-FLOW-011.7
def test_gate_review_allow_open_with_an_open_finding_only_warns_about_a_failing_suite(repo):
    fail_the_suite(repo)
    write_review(repo, "- [ ] R1 **code-gap** reset ignores case\n  - **Decision**: back to code: lower-case the email\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--allow-open")
    c = checks(data)
    assert code == 0 and data["passed"] is True, data
    assert not c["no open finding in review.md"]["ok"] and not c["no open finding in review.md"]["blocking"]
    assert not c[TESTS]["ok"] and not c[TESTS]["blocking"] and "2 failed" in c[TESTS]["details"]
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")  # without --allow-open
    assert code == 1 and checks(data)[TESTS]["blocking"] and not checks(data)[TESTS]["ok"]


# @ac AC-FLOW-011.7
def test_gate_review_allow_open_without_an_open_finding_blocks_on_a_failing_suite(repo):
    fail_the_suite(repo)
    write_review(repo, "- [x] R1 **code-gap** reset ignores case\n  - **Decision**: code fixed\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--allow-open")
    assert code == 1 and checks(data)[TESTS]["blocking"] and not checks(data)[TESTS]["ok"], data


# @ac AC-FLOW-011.8
@pytest.mark.parametrize("allow_open", [[], ["--allow-open"]])
def test_gate_review_needs_a_test_for_every_criterion(repo, allow_open):
    write_tests(repo, "AC-AUTH-003.1", "AC-AUTH-002.1")
    write_review(repo, "- [ ] R1 **test-gap** AC-AUTH-003.2 has no test\n  - **Decision**: back to test: add it\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", *allow_open)
    missing = checks(data)["every acceptance criterion has a test (@ac tag)"]
    assert code == 1 and missing["blocking"] and missing["details"] == ["AC-AUTH-003.2"], data


# @ac AC-FLOW-011.3
def test_gate_review_requires_untagged_files_accounted_for(repo):
    (repo / "src/auth/audit.py").write_text("def audit(): ...\n")
    write_review(repo, "None.\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 1
    assert checks(data)["changed files without tags are accounted for in review.md"]["details"] == ["src/auth/audit.py"]
    write_review(repo, "None.\n\n## Changed files without tags\n\n- `src/auth/audit.py`: logging helper, no behaviour\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 0 and data["passed"] is True


# @ac AC-FLOW-011.3
def test_untagged_files_count_only_as_whole_paths_under_their_heading(repo):
    (repo / "src/auth/audit.py").write_text("def audit(): ...\n")
    not_accounted = [
        "- [x] R1 **quality** `src/auth/audit.py` logs passwords\n  - **Decision**: code fixed\n",  # in a finding only
        "None.\n\n## Changed files without tags\n\n<!-- e.g. `src/auth/audit.py`: helper -->\n",  # in a comment
        "None.\n\n## Changed files without tags\n\n- `src/auth/audit.py.bak`: backup\n",  # a longer path
    ]
    for body in not_accounted:
        write_review(repo, body)
        code, data = run_json("gate", "review", "--change", REF, "--base", "main")
        assert checks(data)["changed files without tags are accounted for in review.md"]["details"] == ["src/auth/audit.py"], body
    write_review(repo, "None.\n\n## Changed files without tags\n\n- src/auth/audit.py (helper of R1, no behaviour)\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 0, data


# @ac AC-FLOW-011.1
def test_gate_review_passes_when_clean(repo):
    write_review(repo, "- [x] R1 **test-gap** AC-AUTH-003.2 only checked the status\n  - **Decision**: code fixed\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 0, data


# @ac AC-FLOW-002.1
def test_review_artifact_has_instructions(repo):
    code, data = run_json("instructions", "review", "--change", REF)
    assert data["outputPath"] == f"spec/changes/{REF}/review.md"
    assert "## Changed files without tags" in data["template"] and "spec-gap" in data["instruction"]


# @ac AC-FLOW-009.6
def test_review_lists_changed_files_with_non_ascii_names(repo):
    # git quotes such names unless asked not to; a quoted name matched no file and the change went unreviewed.
    (repo / "src/auth/café.py").write_text("x = 1\n")
    code, data = run_json("review", "--change", REF, "--base", "main")
    assert findings(data)["untracedSource"] == ["src/auth/café.py"]


# @ac AC-FLOW-010.2
def test_gate_review_blocks_on_an_open_finding_of_unknown_type_even_in_a_build(repo):
    write_review(repo, "- [ ] R1 **spec_gap** lockout also logs\n- [ ] R2 **Design-gap** reset returns None\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--allow-open")
    readable = [c for c in data["checks"] if c["name"].startswith("every finding in review.md is readable")][0]
    assert code == 1 and len(readable["details"]) == 1 and readable["details"][0].startswith("R1: type 'spec_gap' is not one of")  # R2's is known
    write_review(repo, "- [ ] R1 **spec_gap** lockout also logs\n  - **Decision**: back to specify: add REQ-AUTH-004\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--allow-open")
    assert code == 0, data


@pytest.fixture
def on_main(project, monkeypatch):
    """The planned project as a git repo whose work is committed on main: no feature branch."""
    for key, value in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(key, value)
    git(project, "init", "-q", "-b", "main")
    git(project, "add", "spec.yml", "src")
    git(project, "commit", "-q", "-m", "baseline")
    return project


# @ac AC-FLOW-009.5
def test_on_the_base_branch_the_diff_starts_where_the_change_did(on_main):
    git(on_main, "add", "-A")
    git(on_main, "commit", "-q", "-m", "start the change")
    (on_main / "src/auth/stub.py").write_text("def stub(): ...\n")
    git(on_main, "add", "-A")
    git(on_main, "commit", "-q", "-m", "an untagged stub")
    code, data = run_json("review", "--change", REF, "--base", "main")
    assert findings(data)["untracedSource"] == ["src/auth/stub.py"]
    assert data["since"].startswith(f"main at the commit before {REF} started") and data["note"] == ""


# @ac AC-FLOW-011.5
def test_on_the_base_branch_without_a_commit_of_the_change_the_gate_warns(on_main):
    (on_main / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\n")  # specworks: ignore-tags
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--no-run")
    check = next(c for c in data["checks"] if c["name"] == "the change's commits are compared with its base")
    assert not check["ok"] and not check["blocking"]
    assert f"HEAD is on main and no earlier commit marks where {REF} started" in check["details"][0]


# @ac AC-FLOW-011.5
def test_on_a_branch_there_is_no_base_warning(repo):
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--no-run")
    assert not any(c["name"] == "the change's commits are compared with its base" for c in data["checks"])
    assert any(c["name"].endswith("(base main)") for c in data["checks"])


# @ac AC-FLOW-009.5
def test_a_change_from_the_first_commit_has_nothing_to_start_from(project, monkeypatch):
    for key, value in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(key, value)
    git(project, "init", "-q", "-b", "main")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "everything at once")
    code, data = run_json("review", "--change", REF, "--base", "main")
    assert f"HEAD is on main and no earlier commit marks where {REF} started" in data["note"]


def delete_on_the_branch(repo):
    """main gains a test file and a doc; the feature branch then deletes them and a source file."""
    git(repo, "checkout", "-q", "main")
    (repo / "tests").mkdir(exist_ok=True)
    (repo / "tests/test_old.py").write_text("def test_old(): ...\n")
    (repo / "README.md").write_text("docs\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "old test and readme")
    git(repo, "checkout", "-q", "feature")
    git(repo, "merge", "-q", "main")
    for path in ("src/auth/session.py", "tests/test_old.py", "README.md"):
        (repo / path).unlink()


# @ac AC-FLOW-009.7
def test_review_lists_deleted_files(repo):
    delete_on_the_branch(repo)
    code, data = run_json("review", "--change", REF, "--base", "main")
    deleted = {f["path"]: f.get("was") for f in data["changedFiles"] if f["kind"] == "deleted"}
    assert deleted == {"src/auth/session.py": "source", "tests/test_old.py": "test", "README.md": "other"}
    assert findings(data)["deletedFiles"] == ["src/auth/session.py", "tests/test_old.py"]


# @ac AC-FLOW-011.6
def test_gate_review_requires_deleted_files_accounted_for(repo):
    delete_on_the_branch(repo)
    write_review(repo, "None.\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 1
    assert checks(data)["changed files without tags are accounted for in review.md"]["details"] == ["src/auth/session.py", "tests/test_old.py"]
    write_review(repo, "None.\n\n## Changed files without tags\n\n- `src/auth/session.py`: dead code\n- `tests/test_old.py`: its test\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main")
    assert code == 0, data


# @ac AC-FLOW-010.5
def test_a_loose_indented_checkbox_fails_the_review_gate_even_in_a_build(repo):
    write_review(repo, "None.\n\n- Follow-ups:\n  - [ ] reset still ignores case\n")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--allow-open")
    readable = checks(data)["every finding in review.md is readable (- [ ] R<n> ...)"]
    assert code == 1 and not readable["ok"] and readable["blocking"]
