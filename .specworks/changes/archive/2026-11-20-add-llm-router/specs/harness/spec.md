# Spec Delta: harness

## ADDED Requirements

### Requirement: REQ-HARNESS-014 Routing a message that names no peer

A message said in the harness chat that names no peer and replies to no peer's
message SHALL be answered by the skill peer a model chooses for it, from the
skill peers' names and descriptions (REQ-HARNESS-016) and the recent
conversation. When the model chooses no single skill peer (it answers that the
message is for everyone or names no peer that answers, its request fails, has
no key or takes longer than 10 seconds), the peer `onboard` SHALL answer the
message instead, so a message that names no peer is never left unanswered, and
a failed choice SHALL never stop the chat. A message addressed to a peer
(`@<peer>`, REQ-HARNESS-005), a reply to a peer's message and a hand-over
(REQ-HARNESS-003) SHALL reach their peer as before, without asking the model.

#### Scenario: AC-HARNESS-014.1 The chosen peer answers

- **GIVEN** a scripted routing model that answers `refine`
- **WHEN** the user says "let users reset passwords" naming no peer
- **THEN** the peer `refine` runs on that message and its answer replies to it, and no other skill peer runs

#### Scenario: AC-HARNESS-014.2 Meant for everyone

- **GIVEN** a scripted routing model that answers `everyone`
- **WHEN** the user says a message naming no peer
- **THEN** the peer `onboard` answers it, and no other skill peer runs

#### Scenario: AC-HARNESS-014.3 A choice that cannot be used

- **GIVEN** a scripted routing model that names `nobody`, or raises an API error, or answers after the timeout
- **WHEN** the user says a message naming no peer
- **THEN** the peer `onboard` answers it, a warning is logged, and the chat goes on

#### Scenario: AC-HARNESS-014.4 Addressed messages and replies

- **WHEN** the user asks `@test` a question, or replies to a question the peer `refine` asked
- **THEN** `test`, or `refine`, answers it, and the routing model is not asked

#### Scenario: AC-HARNESS-014.5 Hand-overs

- **GIVEN** a scripted `refine` that hands over to `specify`
- **WHEN** the hand-over is said
- **THEN** `specify` runs on it, and the routing model is not asked

### Requirement: REQ-HARNESS-015 The router's model

The routing choice (REQ-HARNESS-014) SHALL be asked of the same model, at the
same base URL and with the same key as the skill peers use (REQ-HARNESS-010,
REQ-HARNESS-012, REQ-HARNESS-013), with no setting of its own. With a stored
Copilot login, each routing request SHALL carry the current Copilot session
token, renewed as the peers' is, and the editor headers the peers' requests
carry. A key's value, and a login's tokens, SHALL never appear in any output,
error, log line, file or message about routing.

#### Scenario: AC-HARNESS-015.1 The peers' model and key

- **GIVEN** `SPECWORKS_MODEL_MODEL`, `SPECWORKS_MODEL_BASE_URL` and `SPECWORKS_MODEL_API_KEY` set
- **WHEN** a message naming no peer is routed
- **THEN** the routing request goes to that base URL, for that model, with that key

#### Scenario: AC-HARNESS-015.2 A Copilot login

- **GIVEN** a stored Copilot login and no `SPECWORKS_MODEL_API_KEY`
- **WHEN** a message naming no peer is routed
- **THEN** the routing request goes to the Copilot API base with the session token and the editor headers

#### Scenario: AC-HARNESS-015.3 A renewed token

- **GIVEN** a stored Copilot login whose session token has expired
- **WHEN** a message naming no peer is routed
- **THEN** a new session token is exchanged first and the routing request carries it, with no login

#### Scenario: AC-HARNESS-015.4 The key never shown

- **GIVEN** a key `sk-secret` and a routing model that fails
- **WHEN** a message naming no peer is routed and the conversation is written
- **THEN** `sk-secret` appears in no reply, log line or `chat.jsonl`, and `onboard` answers

### Requirement: REQ-HARNESS-016 A description per peer

Each skill peer SHALL have a one-paragraph description, the `description` of
its packaged skill's front matter, unchanged, and the routing choice
(REQ-HARNESS-014) SHALL be given each candidate peer's name with its
description.

#### Scenario: AC-HARNESS-016.1 The skill's description

- **WHEN** a harness session is built
- **THEN** the description of every skill peer is its packaged skill's front matter `description`, character for character

#### Scenario: AC-HARNESS-016.2 Given to the model

- **GIVEN** a scripted routing model that records what it is asked
- **WHEN** a message naming no peer is routed
- **THEN** the request names every skill peer with its description, and the message
