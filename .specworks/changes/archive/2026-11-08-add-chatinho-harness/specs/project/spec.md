# Spec Delta: project

## MODIFIED Requirements

### Requirement: REQ-PROJ-030 A change's event log

When the top level's config sets `telemetry.langfuse: true`, recording an
event for a change SHALL append one line of JSON to `events.jsonl` in the
change's folder, holding `at` (the date and time), `event` (its name), the
change's `phase` and the event's own fields, and SHALL make the `.gitignore` in
the change's folder name `events.jsonl` and `events.sent`: written when the
folder has none, and the missing names added, each on its own line, to one it
already has, keeping its other lines. With telemetry off, recording an event
SHALL write nothing. A failure to write the log SHALL never fail the command
that records the event.

#### Scenario: AC-PROJ-030.1 An event recorded

- **GIVEN** a project whose config sets `telemetry.langfuse: true`, and a change in phase `specify`
- **WHEN** the event `gate` is recorded with `passed` false
- **THEN** `events.jsonl` in the change's folder ends with one JSON line holding `at`, `event` `gate`, `phase` `specify` and `passed` false

#### Scenario: AC-PROJ-030.2 Kept out of git

- **GIVEN** a project whose config sets `telemetry.langfuse: true`
- **WHEN** an event is recorded for a change whose folder has no `.gitignore`
- **THEN** the folder gets a `.gitignore` naming `events.jsonl` and `events.sent`, and `git status` does not list `events.jsonl`

#### Scenario: AC-PROJ-030.3 Telemetry off

- **GIVEN** a config with no `telemetry` block, or with `telemetry.langfuse: false`
- **WHEN** an event is recorded for a change
- **THEN** the change's folder has no `events.jsonl` and no new `.gitignore`

#### Scenario: AC-PROJ-030.4 A log that cannot be written

- **GIVEN** a project whose config sets `telemetry.langfuse: true`, and a change whose `events.jsonl` is a folder
- **WHEN** an event is recorded
- **THEN** recording raises no error and the folder is unchanged

#### Scenario: AC-PROJ-030.5 The log moves with the change

- **GIVEN** a change with recorded events
- **WHEN** the change is archived (closed or abandoned)
- **THEN** its archive folder holds the same `events.jsonl` and `.gitignore`

#### Scenario: AC-PROJ-030.6 An existing .gitignore

- **GIVEN** a project whose config sets `telemetry.langfuse: true`, and a change whose `.gitignore` names only `chat.jsonl`
- **WHEN** an event is recorded
- **THEN** the `.gitignore` names `chat.jsonl`, `events.jsonl` and `events.sent`, each once, and recording again adds nothing
