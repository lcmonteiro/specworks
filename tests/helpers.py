"""Shared helpers for tests that need a planned change (proposal, delta spec and tasks)."""

import json
import re
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from specworks.cli import app

runner = CliRunner()
REF = "add-password-reset"

# A sample change: the living spec of user-auth and a planned change that adds and modifies requirements.
LIVING = """\
# user-auth

## Purpose

Lets users prove who they are.

## Requirements

### Requirement: REQ-AUTH-001 Password login
The system SHALL let a user log in with email and password.

#### Scenario: AC-AUTH-001.1 Valid password
- **WHEN** a user submits a correct password
- **THEN** a session is created

### Requirement: REQ-AUTH-002 Lockout
The system SHALL lock an account after 5 failed attempts.

#### Scenario: AC-AUTH-002.1 Fifth failure
- **WHEN** the fifth wrong password is submitted
- **THEN** the account is locked
"""

DELTA = """\
# Spec Delta: user-auth

## ADDED Requirements

### Requirement: REQ-AUTH-003 Password reset
The system SHALL email a single-use reset link valid for 30 minutes.

#### Scenario: AC-AUTH-003.1 Request reset
- **WHEN** a user asks for a reset with a known email
- **THEN** a reset link is emailed

#### Scenario: AC-AUTH-003.2 Expired link
- **GIVEN** a link older than 30 minutes
- **WHEN** it is opened
- **THEN** the user is told it expired

## MODIFIED Requirements

### Requirement: REQ-AUTH-002 Lockout after failures
The system SHALL lock an account after 3 failed attempts.

#### Scenario: AC-AUTH-002.1 Third failure
- **WHEN** the third wrong password is submitted
- **THEN** the account is locked
"""

PROPOSAL = """\
# Proposal: add-password-reset

## Why
Users get locked out.

## What Changes
- Password reset by email

## Capabilities
### Modified Capabilities
- `user-auth`: reset + stricter lockout

## Impact
auth service
"""

TASKS = """\
# Tasks

## 1. Reset

- [ ] 1.1 Write failing tests for AC-AUTH-003.1 and AC-AUTH-003.2; verify they fail
- [ ] 1.2 Implement reset links (REQ-AUTH-003); verify 1.1 passes

## 2. Lockout

- [x] 2.1 Lower the lockout threshold (REQ-AUTH-002); verify AC-AUTH-002.1 test passes
"""


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        pytest.fail(result.output)


def make_planned_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["init", "--dir", "spec", "--no-skills"]).exit_code == 0
    cfg = tmp_path / "spec.yml"
    cfg.write_text(cfg.read_text().replace("capabilities: {}", "capabilities:\n  user-auth:\n    path: src/auth\n    prefix: AUTH"))
    (tmp_path / "src/auth/docs").mkdir(parents=True)
    (tmp_path / "src/auth/docs/spec.md").write_text(LIVING)
    run_json("new", REF)
    change = tmp_path / "spec/changes" / REF
    (change / "proposal.md").write_text(PROPOSAL)
    (change / "specs/user-auth").mkdir(parents=True)
    (change / "specs/user-auth/spec.md").write_text(DELTA)
    (change / "tasks.md").write_text(TASKS)
    return tmp_path


def write_tests(root, *acs):
    (root / "tests").mkdir(exist_ok=True)
    body = "".join(f"# @ac {ac}\ndef test_{ac.lower().replace('-', '_').replace('.', '_')}():\n    assert False\n\n" for ac in acs)
    (root / "tests/test_reset.py").write_text(body)


PASS = f'"{sys.executable}" -c "print(\'ok\')"'


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def make_repo(project, monkeypatch):
    """The planned project as a git repo: baseline on main, the change's work on a feature branch."""
    for key, value in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(key, value)
    cfg = project / "spec.yml"
    cfg.write_text(re.sub(r"(?m)^  test:.*$", lambda _: f"  test: {json.dumps(PASS)}", cfg.read_text(), count=1))
    (project / "src/auth/session.py").write_text("def session(): ...\n")
    git(project, "init", "-q", "-b", "main")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "baseline")
    git(project, "checkout", "-q", "-b", "feature")
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    (project / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\ndef reset(): ...\n")
    (project / "src/auth/lockout.py").write_text("# @req REQ-AUTH-002\nLIMIT = 3\n")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "implement")
    run_json("task", "done", "1.1", "1.2", "--change", REF)
    return project
