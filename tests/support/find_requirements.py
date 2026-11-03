"""Helpers shared by the find_requirements tests of several capabilities."""

from typer.testing import CliRunner

from helpers import init_repo
from specworks.cli import app

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


def line_of(spec, text):
    """The 1-based number of the line of ``spec`` that is exactly ``text``."""
    return spec.splitlines().index(text) + 1


def add_capabilities(config, entries):
    config.write_text(config.read_text(encoding="utf-8").replace("capabilities: {}", "capabilities:\n" + entries), encoding="utf-8")


def make_project(tmp_path, monkeypatch):
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
TOKEN_002 = "The system SHALL refresh a token before it lapses."


def make_tokens_project(tmp_path, monkeypatch):
    """sessions with three living requirements: two mention `token` (each on several lines), one `expired`."""
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    add_capabilities(tmp_path / ".specworks/config.yml", "  sessions:\n    path: src/sessions\n    prefix: SES\n")
    (tmp_path / "src/sessions/docs").mkdir(parents=True)
    (tmp_path / "src/sessions/docs/spec.md").write_text(TOKENS, encoding="utf-8")
    return tmp_path
