"""The specs a change was agreed with: later edits are warned about, and MODIFIED behaviour needs changed tests."""

from helpers import REF, git, run_json

AGREED = "the specs are the ones agreed when specify passed"
MODIFIED_TESTS = "the tests of each MODIFIED requirement changed with it"
DELTA_FILE = f"spec/changes/{REF}/specs/user-auth/spec.md"


def check(data, name):
    found = [c for c in data["checks"] if c["name"] == name]
    return found[0] if found else None


def start_design(project):
    (project / f"spec/changes/{REF}/design.md").write_text("# Design\n\n## Interfaces\n\nNone\n")
    run_json("phase", "specify", "--change", REF)
    code, data = run_json("start", "design", "--change", REF, "--no-run")
    assert code == 0, data


def edit(project, old, new):
    path = project / DELTA_FILE
    path.write_text(path.read_text().replace(old, new))


def test_start_records_the_specs_and_the_gates_warn_when_they_change(project):
    start_design(project)
    meta = (project / f"spec/changes/{REF}/.change.yaml").read_text()
    assert "specified:" in meta and "REQ-AUTH-003:" in meta and "REQ-AUTH-002:" in meta
    code, data = run_json("gate", "design", "--change", REF, "--no-run")
    assert check(data, AGREED)["ok"]

    edit(project, "valid for 30 minutes", "valid for 10 minutes")
    edit(project, "## MODIFIED Requirements", "### Requirement: REQ-AUTH-004 Audit\nThe system SHALL log resets.\n\n"
         "#### Scenario: AC-AUTH-004.1 Logged\n- **WHEN** x\n- **THEN** y\n\n## MODIFIED Requirements")
    code, data = run_json("gate", "design", "--change", REF, "--no-run")
    agreed = check(data, AGREED)
    assert not agreed["ok"] and not agreed["blocking"]
    assert agreed["details"][:2] == ["REQ-AUTH-003 changed", "REQ-AUTH-004 added"]
    assert f"`specworks start design --change {REF}` re-checks specify" in agreed["details"][2]


def test_a_dropped_requirement_is_named(project):
    start_design(project)
    path = project / DELTA_FILE
    path.write_text(path.read_text().split("## MODIFIED Requirements")[0])
    code, data = run_json("gate", "design", "--change", REF, "--no-run")
    assert check(data, AGREED)["details"][0] == "REQ-AUTH-002 dropped"


def test_spacing_and_blank_lines_are_not_a_change(project):
    start_design(project)
    edit(project, "valid for 30 minutes.", "valid  for 30 minutes.\n")
    code, data = run_json("gate", "design", "--change", REF, "--no-run")
    assert check(data, AGREED)["ok"]


def test_going_back_to_design_accepts_the_new_specs(project):
    start_design(project)
    run_json("phase", "code", "--change", REF)
    edit(project, "valid for 30 minutes", "valid for 10 minutes")
    code, data = run_json("start", "design", "--change", REF, "--no-run")
    assert code == 0, data
    code, data = run_json("gate", "design", "--change", REF, "--no-run")
    assert check(data, AGREED)["ok"]


def test_a_change_moved_without_start_is_not_checked(project):
    run_json("phase", "design", "--change", REF)
    code, data = run_json("gate", "design", "--change", REF, "--no-run")
    assert check(data, AGREED) is None


def test_a_modified_requirement_whose_tests_did_not_change_is_named(repo):
    # The lockout test is on main already: the feature branch changes REQ-AUTH-002 (5 -> 3 attempts) but not it.
    git(repo, "checkout", "-q", "main")
    (repo / "tests").mkdir(exist_ok=True)
    (repo / "tests/test_lockout.py").write_text("# @ac AC-AUTH-002.1\ndef test_lockout(): ...\n")  # specworks: ignore-tags
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "lockout test")
    git(repo, "checkout", "-q", "feature")
    git(repo, "merge", "-q", "main")
    reset = repo / "tests/test_reset.py"
    reset.write_text(reset.read_text().replace("# @ac AC-AUTH-002.1\n", ""))  # specworks: ignore-tags
    git(repo, "commit", "-qam", "the lockout test lives in its own file")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--no-run", "--allow-open")
    stale = check(data, MODIFIED_TESTS)
    assert not stale["ok"] and not stale["blocking"]
    assert stale["details"] == ["REQ-AUTH-002: none of its tests changed (tests/test_lockout.py); make sure they check the new behaviour"]

    (repo / "tests/test_lockout.py").write_text("# @ac AC-AUTH-002.1\ndef test_lockout_after_three(): ...\n")  # specworks: ignore-tags
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--no-run", "--allow-open")
    assert check(data, MODIFIED_TESTS)["ok"]


def test_a_modified_title_alone_needs_no_new_test(repo):
    living_block = (repo / "src/auth/docs/spec.md").read_text().split("### Requirement: REQ-AUTH-002 Lockout\n")[1]
    path = repo / DELTA_FILE
    added = path.read_text().split("## MODIFIED Requirements")[0]
    path.write_text(f"{added}## MODIFIED Requirements\n\n### Requirement: REQ-AUTH-002 Lockout after failures\n{living_block}")
    code, data = run_json("gate", "review", "--change", REF, "--base", "main", "--no-run", "--allow-open")
    assert check(data, MODIFIED_TESTS) is None


def test_without_git_the_tests_of_a_modified_requirement_are_not_checked(project):
    code, data = run_json("gate", "review", "--change", REF, "--no-run", "--allow-open")
    assert check(data, MODIFIED_TESTS) is None
