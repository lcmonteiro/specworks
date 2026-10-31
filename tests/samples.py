"""Sample planning text shared by the tests: a living spec, a delta, a proposal and tasks for user-auth."""

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

- [ ] 1.1 [test] Write failing tests for AC-AUTH-003.1 and AC-AUTH-003.2; verify they fail
- [ ] 1.2 [code] Implement reset links (REQ-AUTH-003); verify lint passes

## 2. Lockout

- [x] 2.1 [code] Lower the lockout threshold (REQ-AUTH-002); verify AC-AUTH-002.1 test passes
"""
