"""Finding living requirements by term: `find_requirements` and `spec find`."""

import pytest

from helpers import init_repo
from specworks.cli import app
from specworks.core.errors import ConfigError
from specworks.core.workspace import load_workspace
from specworks.specs.capabilities import BroadTerm, find_requirements, search_requirements
from support.find_requirements import AUTH, TOKEN_002, TOKENS, add_capabilities, line_of, make_project, make_tokens_project, runner

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


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


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


@pytest.fixture
def tokens_project(tmp_path, monkeypatch):
    return make_tokens_project(tmp_path, monkeypatch)


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
