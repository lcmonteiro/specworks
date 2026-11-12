# Spec Delta: harness

## ADDED Requirements

### Requirement: REQ-HARNESS-013 Copilot's default chat model

When the harness uses a stored Copilot login (REQ-HARNESS-012) and neither
`SPECWORKS_MODEL_MODEL` nor `harness.model` names a model, it SHALL ask the
Copilot API, with the session token, for the models the login may use, and
SHALL use the one marked as the default chat model. It SHALL make that request
only then, and before the session starts. When the list cannot be read, or
marks no model as the default chat model, building the model SHALL fail before
the session starts, naming `SPECWORKS_MODEL_MODEL` and `harness.model`, and no
token SHALL appear in the error.

#### Scenario: AC-HARNESS-013.1 Copilot's default used

- **GIVEN** a stored login, no model named, and a model list marking `gpt-4.1` as the default chat model among others
- **WHEN** the harness builds its model
- **THEN** the model is `gpt-4.1`, and the list was asked from the Copilot API base with the session token

#### Scenario: AC-HARNESS-013.2 No request when a model is named

- **GIVEN** a stored login and `harness.model: o3` in the config, or `SPECWORKS_MODEL_MODEL=o3`
- **WHEN** the harness builds its model
- **THEN** the model is `o3` and no model list is asked for

#### Scenario: AC-HARNESS-013.3 No default to use

- **GIVEN** a stored login, no model named, and a model list that marks no default chat model, an answer that is not a model list, or a request that fails
- **WHEN** the harness builds its model
- **THEN** building fails naming `SPECWORKS_MODEL_MODEL` and `harness.model`, and no token appears in the error

## MODIFIED Requirements

### Requirement: REQ-HARNESS-010 The model from the environment

The harness SHALL use the model named by `SPECWORKS_MODEL_MODEL`, or, when that
variable is missing or empty, by `harness.model` in the top level's config, or,
when neither names one and a stored Copilot login is used, Copilot's default
chat model (REQ-HARNESS-013), with the key in `SPECWORKS_MODEL_API_KEY`, or,
when that key is missing or empty, the key of a stored Copilot login
(REQ-HARNESS-012), at `SPECWORKS_MODEL_BASE_URL` when it is set, through an
OpenAI-compatible API. No model from any of these SHALL be an error naming
`SPECWORKS_MODEL_MODEL` and `harness.model`. A missing or empty key with no
stored login SHALL be an error naming `SPECWORKS_MODEL_API_KEY` and saying to
run `specworks login copilot`. Both SHALL be raised before the session starts. A key's value, and a
login's tokens, SHALL never appear in any output, error, file or message.

#### Scenario: AC-HARNESS-010.1 Read from the environment

- **GIVEN** the three variables set
- **WHEN** the harness builds its model
- **THEN** the model uses that name, that base URL and that key

#### Scenario: AC-HARNESS-010.2 A missing variable

- **WHEN** `SPECWORKS_MODEL_API_KEY` is set and neither `SPECWORKS_MODEL_MODEL` nor `harness.model` names a model, or `SPECWORKS_MODEL_API_KEY` is missing or empty and no login is stored
- **THEN** building fails with an error naming `SPECWORKS_MODEL_MODEL` and `harness.model`, or, for the key, naming `SPECWORKS_MODEL_API_KEY` and saying to run `specworks login copilot`

#### Scenario: AC-HARNESS-010.3 The key never shown

- **GIVEN** a key `sk-secret` and a model that fails
- **WHEN** a peer runs and the conversation is written
- **THEN** `sk-secret` appears in no reply, error, log line or `chat.jsonl`

#### Scenario: AC-HARNESS-010.4 A login's tokens never shown

- **GIVEN** a stored login whose OAuth token is `gho_secret`, a session token `tid=secret`, and a model that fails
- **WHEN** a peer runs and the conversation is written
- **THEN** neither token appears in any reply, error, log line or `chat.jsonl`

#### Scenario: AC-HARNESS-010.5 The model from the config

- **GIVEN** `harness.model: gpt-4.1` in the top level's config, `SPECWORKS_MODEL_MODEL` unset and `SPECWORKS_MODEL_API_KEY` set
- **WHEN** the harness builds its model
- **THEN** the model is `gpt-4.1`

#### Scenario: AC-HARNESS-010.6 The variable wins over the config

- **GIVEN** `harness.model: gpt-4.1` in the config and `SPECWORKS_MODEL_MODEL=o3`
- **WHEN** the harness builds its model
- **THEN** the model is `o3`
