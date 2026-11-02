"""Finding living requirements by term: `find_requirements` and `spec find`."""

import json

import pytest
from typer.testing import CliRunner

from helpers import init_repo
from specworks.cli import app
from specworks.core.errors import ConfigError
from specworks.core.workspace import load_workspace
from specworks.specs.capabilities import BroadTerm, find_requirements, search_requirements

runner = CliRunner()

AUTH = """\
# user-auth

## Purpose

Lets users prove who they are.

## Requirements

### Requirement: REQ-AUTH-001 Password login
The system SHALL let a user log in with email and password.

#### Scenario: AC-AUTH-001.1 Valid password
- **WHEN** a user submits a correct password
- **THEN** a session is created

### Requirement: REQ-AUTH-002 A branch per change
The system SHALL create a branch per change unless `--no-branch` is given.

#### Scenario: AC-AUTH-002.1 Without a branch
- **WHEN** a change is created with `--no-branch`
- **THEN** it stays on the current branch

### Requirement: REQ-AUTH-003 Reset link
The system SHALL email a reset link.

#### Scenario: AC-AUTH-003.1 Expired link
- **WHEN** a link older than 30 minutes is opened
- **THEN** the user is told it expired
"""

SETTINGS = """\
# settings

## Purpose

The project's settings.

## Requirements

### Requirement: REQ-SET-001 Setting a value
The system SHALL write a value with `config set <key> <value>`.

#### Scenario: AC-SET-001.1 A known key
- **WHEN** a known key is set
- **THEN** the config holds the value

### Requirement: REQ-SET-002 Reading a value
The system SHALL print a value with `config get <key>`.

#### Scenario: AC-SET-002.1 A known key
- **WHEN** a known key is read
- **THEN** its value is printed

### Requirement: REQ-SET-003 Module settings
The system SHALL write a module's value with `config set --module <name>`.

#### Scenario: AC-SET-003.1 In a module
- **WHEN** a key is set for a module
- **THEN** the module's config holds the value
"""

INVOICES = """\
# invoices

## Purpose

Bills customers.

## Requirements

### Requirement: REQ-INV-001 Monthly invoice
The system SHALL send an invoice on the first day of each month.

#### Scenario: AC-INV-001.1 First day
- **WHEN** a month starts
- **THEN** every customer gets an invoice
"""


def line_of(spec, text):
    """The 1-based number of the line of ``spec`` that is exactly ``text``."""
    return spec.splitlines().index(text) + 1


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        pytest.fail(result.output)


def add_capabilities(config, entries):
    config.write_text(config.read_text(encoding="utf-8").replace("capabilities: {}", "capabilities:\n" + entries), encoding="utf-8")


@pytest.fixture
def project(tmp_path, monkeypatch):
    """user-auth and settings with living specs, and audit-log with none yet."""
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    add_capabilities(
        tmp_path / ".specworks/config.yml",
        "  user-auth:\n    path: src/auth\n    prefix: AUTH\n  settings:\n    path: src/settings\n    prefix: SET\n  audit-log:\n    path: src/audit\n    prefix: AUDIT\n",
    )
    for folder, spec in (("src/auth", AUTH), ("src/settings", SETTINGS)):
        (tmp_path / folder / "docs").mkdir(parents=True)
        (tmp_path / folder / "docs/spec.md").write_text(spec, encoding="utf-8")
    return tmp_path


def find(root, terms):
    return find_requirements(load_workspace(root), terms)


# @ac AC-SPECS-016.1
def test_ac_specs_016_1_a_term_in_a_requirements_text_is_found_ignoring_case(project):
    matches = find(project, ["--NO-BRANCH"])
    assert [(m.capability, m.id, m.title) for m in matches] == [("user-auth", "REQ-AUTH-002", "A branch per change")]
    text = "The system SHALL create a branch per change unless `--no-branch` is given."
    assert matches[0].path == "src/auth/docs/spec.md"
    assert matches[0].line == line_of(AUTH, text)  # the first matching line, not the scenario's that mentions it again
    assert matches[0].text == text


# @ac AC-SPECS-016.1
def test_ac_specs_016_1_a_term_in_the_title_matches_the_header_line(project):
    (match,) = find(project, ["reset LINK"])
    assert match.id == "REQ-AUTH-003"
    assert match.line == line_of(AUTH, "### Requirement: REQ-AUTH-003 Reset link")
    assert match.text == "### Requirement: REQ-AUTH-003 Reset link"


# @ac AC-SPECS-016.2
def test_ac_specs_016_2_a_term_only_in_a_scenario_matches_the_scenarios_line(project):
    (match,) = find(project, ["30 minutes"])
    assert (match.capability, match.id, match.title) == ("user-auth", "REQ-AUTH-003", "Reset link")
    assert match.line == line_of(AUTH, "- **WHEN** a link older than 30 minutes is opened")
    assert match.text == "- **WHEN** a link older than 30 minutes is opened"


# @ac AC-SPECS-016.3
def test_ac_specs_016_3_several_terms_list_each_requirement_once(project):
    matches = find(project, ["30 minutes", "--no-branch"])  # --no-branch is on two lines of REQ-AUTH-002
    assert [m.id for m in matches] == ["REQ-AUTH-002", "REQ-AUTH-003"]  # requirement order, not term order


# @ac AC-SPECS-016.3
def test_ac_specs_016_3_two_terms_in_one_requirement_list_it_once_with_the_first_matching_line(project):
    (match,) = find(project, ["stays on the current", "unless"])
    assert match.id == "REQ-AUTH-002"
    assert match.line == line_of(AUTH, "The system SHALL create a branch per change unless `--no-branch` is given.")


# @ac AC-SPECS-016.3
def test_ac_specs_016_3_matches_come_in_capability_then_requirement_order(project):
    matches = find(project, ["SHALL"])
    assert [(m.capability, m.id) for m in matches] == [
        ("user-auth", "REQ-AUTH-001"),
        ("user-auth", "REQ-AUTH-002"),
        ("user-auth", "REQ-AUTH-003"),
        ("settings", "REQ-SET-001"),
        ("settings", "REQ-SET-002"),
        ("settings", "REQ-SET-003"),
    ]  # audit-log has no living spec yet and is skipped


# @ac AC-SPECS-016.4
def test_ac_specs_016_4_a_modules_capability_is_listed_under_its_ref(project):
    assert runner.invoke(app, ["module", "add", "services/billing"]).exit_code == 0
    add_capabilities(project / "services/billing/.specworks/config.yml", "  invoices:\n    path: src/invoices\n    prefix: INV\n")
    (project / "services/billing/src/invoices/docs").mkdir(parents=True)
    (project / "services/billing/src/invoices/docs/spec.md").write_text(INVOICES, encoding="utf-8")
    matches = find(project, ["first day"])
    assert [(m.capability, m.id, m.title) for m in matches] == [("billing:invoices", "REQ-INV-001", "Monthly invoice")]
    assert matches[0].path == "services/billing/src/invoices/docs/spec.md"
    assert matches[0].line == line_of(INVOICES, "The system SHALL send an invoice on the first day of each month.")


# @ac AC-SPECS-016.5
def test_ac_specs_016_5_no_match_is_empty(project):
    assert find(project, ["nothing-like-this"]) == []


# @ac AC-SPECS-016.6
@pytest.mark.parametrize(("terms", "named"), [([""], "''"), (["   "], "'   '"), (["--no-branch", ""], "''")])
def test_ac_specs_016_6_an_empty_term_is_refused_naming_it(project, terms, named):
    with pytest.raises(ConfigError) as error:
        find(project, terms)
    assert str(error.value) == f"empty search term: {named}"


SET_001 = "The system SHALL write a value with `config set <key> <value>`."
SET_003 = "The system SHALL write a module's value with `config set --module <name>`."


def config_set_lines():
    return [
        f"settings  REQ-SET-001  Setting a value  src/settings/docs/spec.md:{line_of(SETTINGS, SET_001)}",
        f"settings  REQ-SET-003  Module settings  src/settings/docs/spec.md:{line_of(SETTINGS, SET_003)}",
    ]


# @ac AC-CLI-016.1
def test_ac_cli_016_1_matches_print_one_line_each(project):
    result = runner.invoke(app, ["spec", "find", "config set"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == config_set_lines()


# @ac AC-CLI-016.2
def test_ac_cli_016_2_matches_as_json_with_paths_relative_to_the_workspace_root(project, monkeypatch):
    monkeypatch.chdir(project / "src")  # paths are the workspace root's, not the current folder's
    code, data = run_json("spec", "find", "config set")
    assert code == 0, data
    assert data["terms"] == ["config set"]
    assert data["matches"] == [
        {
            "capability": "settings",
            "id": "REQ-SET-001",
            "title": "Setting a value",
            "path": "src/settings/docs/spec.md",
            "line": line_of(SETTINGS, SET_001),
            "text": SET_001,
        },
        {
            "capability": "settings",
            "id": "REQ-SET-003",
            "title": "Module settings",
            "path": "src/settings/docs/spec.md",
            "line": line_of(SETTINGS, SET_003),
            "text": SET_003,
        },
    ]


# @ac AC-CLI-016.3
def test_ac_cli_016_3_no_match_prints_a_line_and_exits_0(project):
    result = runner.invoke(app, ["spec", "find", "nothing-like-this"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "no requirement mentions nothing-like-this"


# @ac AC-CLI-016.3
def test_ac_cli_016_3_no_match_lists_every_term(project):
    result = runner.invoke(app, ["spec", "find", "nothing-like-this", "nor-this"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "no requirement mentions nothing-like-this, nor-this"


# @ac AC-CLI-016.3
def test_ac_cli_016_3_no_match_as_json_has_empty_matches(project):
    code, data = run_json("spec", "find", "nothing-like-this")
    assert code == 0, data
    assert data == {"terms": ["nothing-like-this"], "matches": [], "broad": []}


# @ac AC-CLI-016.4
def test_ac_cli_016_4_no_term_is_refused(project):
    code, data = run_json("spec", "find")
    assert code == 1
    assert set(data) == {"error"} and "give at least one term" in data["error"]


MARKUP = """\
# user-auth

## Purpose

Lets users prove who they are.

## Requirements

### Requirement: REQ-AUTH-001 Password login
The system SHALL let a user log in with email and password.

#### Scenario: AC-AUTH-001.1 Valid password
- **GIVEN** a registered user
- **WHEN** a correct password is submitted
- **THEN** a session is created
- **AND** the user is greeted

### Requirement: REQ-AUTH-002 A reset link
The system SHALL refuse a reset link when the link expires.

#### Scenario: AC-AUTH-002.1 An old link
- **WHEN** a link older than 30 minutes is opened
- **THEN** the user is told it expired
"""

MARKUP_WHEN = "The system SHALL refuse a reset link when the link expires."


@pytest.fixture
def markup_project(tmp_path, monkeypatch):
    """user-auth only: its words say "requirement", "scenario" or "when" only in the markup, except REQ-AUTH-002's text."""
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    add_capabilities(tmp_path / ".specworks/config.yml", "  user-auth:\n    path: src/auth\n    prefix: AUTH\n")
    (tmp_path / "src/auth/docs").mkdir(parents=True)
    (tmp_path / "src/auth/docs/spec.md").write_text(MARKUP, encoding="utf-8")
    return tmp_path


def search(root, terms):
    return search_requirements(load_workspace(root), terms)


# @ac AC-SPECS-016.7
@pytest.mark.parametrize("term", ["requirement", "Scenario", "REQUIREMENT:"])
def test_ac_specs_016_7_the_heading_keywords_find_nothing(markup_project, term):
    assert search(markup_project, [term]).matches == []
    assert find(markup_project, [term]) == []


# @ac AC-SPECS-016.7
def test_ac_specs_016_7_when_finds_only_the_requirement_whose_text_says_it(markup_project):
    (match,) = search(markup_project, ["when"]).matches  # not REQ-AUTH-001, whose only "when" is its **WHEN** step
    assert (match.capability, match.id, match.title) == ("user-auth", "REQ-AUTH-002", "A reset link")
    assert match.line == line_of(MARKUP, MARKUP_WHEN)
    assert match.text == MARKUP_WHEN
    assert find(markup_project, ["WHEN"]) == [match]


# @ac AC-SPECS-016.7
@pytest.mark.parametrize("term", ["given", "**THEN**"])
def test_ac_specs_016_7_the_step_labels_find_nothing(markup_project, term):
    assert search(markup_project, [term]).matches == []


# @ac AC-SPECS-016.7
def test_ac_specs_016_7_an_id_and_a_scenario_title_still_match(markup_project):
    (by_id,) = search(markup_project, ["req-auth-002"]).matches
    assert by_id.id == "REQ-AUTH-002"
    assert by_id.line == line_of(MARKUP, "### Requirement: REQ-AUTH-002 A reset link")
    assert by_id.text == "### Requirement: REQ-AUTH-002 A reset link"  # the whole stripped line, as before
    (by_title,) = search(markup_project, ["an old link"]).matches
    assert by_title.id == "REQ-AUTH-002"
    assert by_title.line == line_of(MARKUP, "#### Scenario: AC-AUTH-002.1 An old link")
    (by_step,) = search(markup_project, ["30 minutes"]).matches
    assert by_step.text == "- **WHEN** a link older than 30 minutes is opened"


TOKENS = """\
# sessions

## Purpose

Keeps users signed in.

## Requirements

### Requirement: REQ-SES-001 Signing in
The system SHALL issue a token at login.

#### Scenario: AC-SES-001.1 At login
- **WHEN** a user logs in
- **THEN** a token is returned

### Requirement: REQ-SES-002 Staying signed in
The system SHALL refresh a token before it lapses.

#### Scenario: AC-SES-002.1 Before it lapses
- **WHEN** a token is close to lapsing
- **THEN** a new one is returned

### Requirement: REQ-SES-003 Signing out
The system SHALL end the session once it has expired.

#### Scenario: AC-SES-003.1 Expired session
- **WHEN** the session has expired
- **THEN** the user must log in again
"""

TOKEN_001 = "The system SHALL issue a token at login."
TOKEN_002 = "The system SHALL refresh a token before it lapses."


@pytest.fixture
def tokens_project(tmp_path, monkeypatch):
    """sessions with three living requirements: two mention `token` (each on several lines), one `expired`."""
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    add_capabilities(tmp_path / ".specworks/config.yml", "  sessions:\n    path: src/sessions\n    prefix: SES\n")
    (tmp_path / "src/sessions/docs").mkdir(parents=True)
    (tmp_path / "src/sessions/docs/spec.md").write_text(TOKENS, encoding="utf-8")
    return tmp_path


# @ac AC-SPECS-016.8
def test_ac_specs_016_8_a_term_matching_more_than_half_is_broad(tokens_project):
    result = search(tokens_project, ["token", "expired"])
    assert [m.id for m in result.matches] == ["REQ-SES-001", "REQ-SES-002", "REQ-SES-003"]  # all still listed
    assert result.broad == [BroadTerm(term="token", matches=2, of=3)]  # each requirement once; expired (1 of 3) is not broad
    assert result.searched == 3


# @ac AC-SPECS-016.8
def test_ac_specs_016_8_a_term_counts_a_requirement_whose_first_line_another_term_found(tokens_project):
    result = search(tokens_project, ["signing IN", "Token"])  # REQ-SES-001's header is found by "signing in", before its token line
    assert [(m.id, m.line) for m in result.matches] == [
        ("REQ-SES-001", line_of(TOKENS, "### Requirement: REQ-SES-001 Signing in")),
        ("REQ-SES-002", line_of(TOKENS, TOKEN_002)),
    ]
    assert result.broad == [BroadTerm(term="Token", matches=2, of=3)]  # the term as given; "signing in" is 1 of 3


# @ac AC-SPECS-016.8
def test_ac_specs_016_8_no_term_is_broad_when_no_requirement_is_searched(project):
    (project / "src/auth/docs/spec.md").unlink()
    (project / "src/settings/docs/spec.md").unlink()
    result = search(project, ["token"])
    assert (result.matches, result.broad, result.searched) == ([], [], 0)


TOKEN_WARNING = "warning: 'token' matches 2 of 3 requirements; try a narrower term"


# @ac AC-CLI-016.5
def test_ac_cli_016_5_a_broad_term_prints_the_matches_and_a_warning(tokens_project):
    result = runner.invoke(app, ["spec", "find", "token"])
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[:2] == [
        f"sessions  REQ-SES-001  Signing in  src/sessions/docs/spec.md:{line_of(TOKENS, TOKEN_001)}",
        f"sessions  REQ-SES-002  Staying signed in  src/sessions/docs/spec.md:{line_of(TOKENS, TOKEN_002)}",
    ]
    assert lines[2:] == [TOKEN_WARNING]


# @ac AC-CLI-016.5
def test_ac_cli_016_5_a_broad_term_is_listed_in_broad_as_json(tokens_project):
    code, data = run_json("spec", "find", "token", "expired")
    assert code == 0, data
    assert [m["id"] for m in data["matches"]] == ["REQ-SES-001", "REQ-SES-002", "REQ-SES-003"]
    assert data["broad"] == [{"term": "token", "matches": 2, "of": 3}]


# @ac AC-CLI-016.5
def test_ac_cli_016_5_a_narrow_term_has_no_warning_and_an_empty_broad(tokens_project):
    result = runner.invoke(app, ["spec", "find", "expired"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [f"sessions  REQ-SES-003  Signing out  src/sessions/docs/spec.md:{line_of(TOKENS, 'The system SHALL end the session once it has expired.')}"]
    code, data = run_json("spec", "find", "expired")
    assert code == 0, data
    assert data["broad"] == []
