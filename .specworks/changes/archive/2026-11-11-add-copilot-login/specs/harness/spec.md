# Spec Delta: harness

## ADDED Requirements

### Requirement: REQ-HARNESS-011 The Copilot login

The harness SHALL let a user log in to GitHub Copilot with GitHub's device flow:
it SHALL show the verification address and the one-time code, wait until the user
authorises, and keep only the resulting long-lived OAuth token, readable by its
owner only, together with the GitHub Enterprise host when one is given. A login
SHALL have a scope: global, found from every project, or local, found only from
the project it was made in. A local login SHALL be kept outside the project's
folder, so no token is ever written inside the project. Logging in again in a
scope that holds a login that still gives a Copilot session token SHALL reuse it
without the device flow, unless forced; a stored login that no longer gives one
SHALL be replaced by a new device flow. A flow that is denied, or whose code
expires, SHALL fail and leave any earlier login as it was. No token, OAuth or
session, SHALL appear in any output, error or log.

#### Scenario: AC-HARNESS-011.1 A global login

- **WHEN** a user logs in with global scope and authorises in the device flow
- **THEN** the OAuth token is stored, readable by its owner only, and a project in any folder finds it

#### Scenario: AC-HARNESS-011.2 A local login

- **GIVEN** projects `a` and `b`
- **WHEN** a user logs in with local scope from project `a`
- **THEN** project `a` finds the login, project `b` does not, and no file is written inside `a`'s folder

#### Scenario: AC-HARNESS-011.3 An existing login is reused

- **GIVEN** a stored login in the chosen scope whose token still gives a session token
- **WHEN** the user logs in again in that scope
- **THEN** no device flow starts, the result says the login was reused, and the stored login is unchanged

#### Scenario: AC-HARNESS-011.4 A forced login

- **GIVEN** a stored login that still works
- **WHEN** the user logs in again, forcing it
- **THEN** a device flow runs and its token replaces the stored one

#### Scenario: AC-HARNESS-011.5 A stale login

- **GIVEN** a stored login whose token GitHub no longer accepts
- **WHEN** the user logs in again
- **THEN** a device flow runs and its token replaces the stored one

#### Scenario: AC-HARNESS-011.6 A flow that does not finish

- **GIVEN** a stored login
- **WHEN** a new device flow (forced) is denied, or its code expires
- **THEN** the login fails with an error and the earlier login is unchanged

#### Scenario: AC-HARNESS-011.7 GitHub Enterprise

- **WHEN** a user logs in with the host `example.ghe.com`
- **THEN** the device flow and every later token exchange go to that host, and the host is kept with the login

#### Scenario: AC-HARNESS-011.8 No token shown

- **GIVEN** an OAuth token `gho_secret` and a session token `tid=secret`
- **WHEN** a login runs, succeeds or fails
- **THEN** neither token appears in any output, error or log line

### Requirement: REQ-HARNESS-012 The model from a stored login

When `SPECWORKS_MODEL_API_KEY` is missing or empty, the harness SHALL use the
Copilot login stored for the project (REQ-HARNESS-011), the project's local one
before the global one, and SHALL use the Copilot API as the base URL, unless
`SPECWORKS_MODEL_BASE_URL` is set. Its key SHALL be a Copilot session token
exchanged from the OAuth token, never stored, and renewed before it expires, so
a chat that runs longer than one token's life goes on without a new login. The
harness SHALL NOT read or use any stored login when `SPECWORKS_MODEL_API_KEY` is
set. A stored login that can no longer give a session token SHALL be an error,
raised before the session starts when it is already known then, saying to run
`specworks login copilot` again, without any token.

#### Scenario: AC-HARNESS-012.1 The key from the login

- **GIVEN** a stored login, `SPECWORKS_MODEL_MODEL` set and `SPECWORKS_MODEL_API_KEY` unset
- **WHEN** the harness builds its model
- **THEN** the model uses that name, the Copilot API base and the session token exchanged from the stored OAuth token

#### Scenario: AC-HARNESS-012.2 Local before global

- **GIVEN** a global login and a local login of the project, for different accounts
- **WHEN** the harness builds its model
- **THEN** the session token is the one exchanged from the local login's token

#### Scenario: AC-HARNESS-012.3 An explicit key wins

- **GIVEN** `SPECWORKS_MODEL_API_KEY` set and a stored login
- **WHEN** the harness builds its model
- **THEN** the model uses the variable's key, and no stored login is read and no exchange is made

#### Scenario: AC-HARNESS-012.4 A long chat

- **GIVEN** a session token that expires in 25 minutes
- **WHEN** a request is sent after it has expired
- **THEN** a new session token is exchanged first and the request is sent with it, with no login

#### Scenario: AC-HARNESS-012.5 A login that no longer works

- **GIVEN** a stored login whose token GitHub rejects
- **WHEN** the harness needs a session token
- **THEN** it fails with an error saying to run `specworks login copilot` again, and no token appears in it

#### Scenario: AC-HARNESS-012.6 The base URL set by the user

- **GIVEN** a stored login and `SPECWORKS_MODEL_BASE_URL` set
- **WHEN** the harness builds its model
- **THEN** the model's base URL is the variable's value

## MODIFIED Requirements

### Requirement: REQ-HARNESS-010 The model from the environment

The harness SHALL use the model named by `SPECWORKS_MODEL_MODEL` with the key in
`SPECWORKS_MODEL_API_KEY`, or, when that key is missing or empty, the key of a
stored Copilot login (REQ-HARNESS-012), at `SPECWORKS_MODEL_BASE_URL` when it is
set, through an OpenAI-compatible API. A missing or empty model SHALL be an error
naming the variable. A missing or empty key with no stored login SHALL be an
error naming `SPECWORKS_MODEL_API_KEY` and saying to run `specworks login
copilot`. Both SHALL be raised before the session starts. A key's value, and a
login's tokens, SHALL never appear in any output, error, file or message.

#### Scenario: AC-HARNESS-010.1 Read from the environment

- **GIVEN** the three variables set
- **WHEN** the harness builds its model
- **THEN** the model uses that name, that base URL and that key

#### Scenario: AC-HARNESS-010.2 A missing variable

- **WHEN** `SPECWORKS_MODEL_MODEL` is missing or empty, or `SPECWORKS_MODEL_API_KEY` is missing or empty and no login is stored
- **THEN** building fails with an error naming that variable, and, for the key, saying to run `specworks login copilot`

#### Scenario: AC-HARNESS-010.3 The key never shown

- **GIVEN** a key `sk-secret` and a model that fails
- **WHEN** a peer runs and the conversation is written
- **THEN** `sk-secret` appears in no reply, error, log line or `chat.jsonl`

#### Scenario: AC-HARNESS-010.4 A login's tokens never shown

- **GIVEN** a stored login whose OAuth token is `gho_secret`, a session token `tid=secret`, and a model that fails
- **WHEN** a peer runs and the conversation is written
- **THEN** neither token appears in any reply, error, log line or `chat.jsonl`
