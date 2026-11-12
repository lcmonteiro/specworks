"""
Finding living requirements by term: `find_requirements` and `spec find`.
"""

import json

import pytest

from specworks.cli import app
from support.find_requirements import SETTINGS, TOKEN_002, TOKENS, line_of, make_project, make_tokens_project, runner


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        pytest.fail(result.output)


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


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

TOKEN_001 = "The system SHALL issue a token at login."


@pytest.fixture
def tokens_project(tmp_path, monkeypatch):
    return make_tokens_project(tmp_path, monkeypatch)


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
