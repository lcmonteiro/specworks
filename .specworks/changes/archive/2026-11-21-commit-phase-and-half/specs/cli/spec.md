# Spec Delta: cli

## MODIFIED Requirements

### Requirement: REQ-CLI-012 commit

`specworks commit --change <ref>` SHALL commit the change's phase
(REQ-PROJ-024), the active change of that name or, when there is none, the
newest archived one, with `--half test|code` for the half of implement and
`--message` for the text after the subject's prefix (REQ-PROJ-036),
`--trailer` (repeatable) for the trailers and `--json`. It SHALL print the
commit's short hash and subject, the files committed, and the files left out,
each relative to the workspace root; under `--json` it SHALL return them as
`commit` (null when nothing was committed), `subject`, `committed`, `leftOut`
and `alreadyDirty`. With
telemetry `on`, after committing it SHALL send the change's unsent events
(REQ-INTEG-009) and print how many were sent, or why they were not and how
many are queued, with the hint `specworks telemetry push`; under `--json` as
`telemetry` (`sent`, `queued`, `reason`), null when telemetry is not `on`. A
failure to send SHALL NOT change its exit code. A refusal
SHALL be an error (`{"error": …}` with exit 1 under `--json`).

#### Scenario: AC-CLI-012.1 A commit

- **WHEN** `commit --change add-login --trailer "Co-Authored-By: A <a@x>" --json` runs with phase files changed
- **THEN** it exits 0 and returns the commit, the committed and left-out paths relative to the workspace root, and `git log` shows the subject and trailer

#### Scenario: AC-CLI-012.2 Nothing to commit

- **WHEN** `commit --change add-login --json` runs with nothing changed since the record
- **THEN** it exits 0 with `commit` null and an empty `committed`

#### Scenario: AC-CLI-012.3 An unknown change

- **WHEN** `commit --change nope --json` runs
- **THEN** it prints `{"error": …}` naming `nope` and exits 1, when `nope` is neither an active nor an archived change

#### Scenario: AC-CLI-012.4 An archived change

- **GIVEN** a change `add-login` that close has just archived
- **WHEN** `commit --change add-login --json` runs
- **THEN** it exits 0 and returns the commit with the subject `add-login: close`

#### Scenario: AC-CLI-012.5 Events sent after the commit

- **GIVEN** telemetry `on` with a server that accepts every batch, and a change with unsent events
- **WHEN** `commit --change add-login --json` runs
- **THEN** it exits 0, the commit holds neither `events.jsonl` nor `events.sent`, and `telemetry` has `queued` 0 and `sent` counting every unsent event, the `commit` event included

#### Scenario: AC-CLI-012.6 Langfuse unreachable

- **GIVEN** telemetry `on` with a server that answers 500
- **WHEN** `commit --change add-login` runs with phase files changed
- **THEN** it exits 0, the commit is made, and the output says the events were not sent, how many are queued, and `specworks telemetry push`

#### Scenario: AC-CLI-012.7 Telemetry not on

- **GIVEN** a config with no `telemetry` block
- **WHEN** `commit --change add-login --json` runs
- **THEN** `telemetry` is null and no request is made

#### Scenario: AC-CLI-012.8 The half and a message

- **GIVEN** a change `add-login` in implement with changed files
- **WHEN** `commit --change add-login --half code --message "cycle 2" --json` runs
- **THEN** it exits 0 and `subject` is `add-login: implement (code) - cycle 2`, as `git log` shows

#### Scenario: AC-CLI-012.9 No half in implement

- **GIVEN** a change `add-login` in implement with changed files
- **WHEN** `commit --change add-login --json` runs
- **THEN** it prints `{"error": …}` naming `--half test` and `--half code`, exits 1, and no commit is made
