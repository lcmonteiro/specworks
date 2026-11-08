# Spec Delta: harness

## MODIFIED Requirements

### Requirement: REQ-HARNESS-009 The conversation kept

The backend SHALL append every message of the chat, one JSON line each with its
id, sender, addressee, reply, status and text, to `chat.jsonl` in the run's
change folder, and SHALL make the change folder's `.gitignore` name
`chat.jsonl`. A run SHALL start with no change and an empty conversation. Until
the run has a change, the backend SHALL hold the messages and write them, in
order, once the run's change is known: the first active change whose folder
changes during the run, whether it was created during the run or existed
before. A new run SHALL NOT load an earlier conversation. A failure to write
SHALL never stop the chat.

#### Scenario: AC-HARNESS-009.1 Appended

- **GIVEN** a run on change `add-x`
- **WHEN** the user says something and a peer replies
- **THEN** `chat.jsonl` in `add-x`'s folder ends with those two messages, and `git status` does not list it

#### Scenario: AC-HARNESS-009.2 Before the change exists

- **GIVEN** a run started with no change
- **WHEN** the user asks `refine` to start one and a peer creates the change `add-x` during the run
- **THEN** `add-x`'s `chat.jsonl` holds every message from the user's first one on, in order

#### Scenario: AC-HARNESS-009.4 A log that cannot be written

- **GIVEN** a change whose `chat.jsonl` is a folder
- **WHEN** a message is said
- **THEN** the chat goes on and the message is delivered

#### Scenario: AC-HARNESS-009.5 An existing change continued

- **GIVEN** an active change `add-x` whose `chat.jsonl` holds an earlier conversation
- **WHEN** a new run starts and a peer writes a file in `add-x`'s folder
- **THEN** the peers' memory did not hold the earlier conversation, and `add-x`'s `chat.jsonl` gains every message of this run after the earlier ones
