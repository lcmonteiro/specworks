# Spec Delta: cli

## ADDED Requirements

### Requirement: REQ-CLI-017 Events the commands record

When telemetry is opted in (REQ-PROJ-030), each command below that acts on a
change SHALL record one event for it once it has run, whether its check passed
or failed, with `ms`, its duration in milliseconds, and only these fields:
`new` (none); `phase` (`from`, `to`); `start` (`to`, `started`); `gate`
(`gate`, `passed`, `failed`: the names of the failed checks); `run` with
`--change` (`key`, `exitCode`); `finding add|decide|done|close` (`action`,
`id`, `type`, `step`); `cycle` (`phases`, `open`: the number of open findings);
`validate` (`verdict`, `critical`, `warnings`); `commit` (`committed`: the
number of files, `made`: whether a commit was created); `close` (`merged`: the
number of capabilities); `abandon` (none). A command refused with an error
SHALL record nothing. No event SHALL hold text from a file, a finding, a reason
or a command's output.

#### Scenario: AC-CLI-017.1 A failed gate

- **GIVEN** a project with `telemetry.langfuse: true` and a change whose `gate specify` fails on one check
- **WHEN** `gate specify --change <ref>` runs
- **THEN** it exits 1 and the change's `events.jsonl` ends with a `gate` event with `gate` `specify`, `passed` false, `failed` naming that check, and `ms`

#### Scenario: AC-CLI-017.2 Each command's event

- **GIVEN** a project with `telemetry.langfuse: true`
- **WHEN** `new`, `phase`, `start`, `run test --change`, `finding add`, `cycle`, `validate`, `commit`, `close` and `abandon` run on changes
- **THEN** each adds one event of its name with exactly the fields listed for it, plus `at`, `phase` and `ms`

#### Scenario: AC-CLI-017.3 No content

- **GIVEN** a project with `telemetry.langfuse: true`
- **WHEN** `finding add code "secret text" --proposal "other text"` and `abandon --reason "why text"` run
- **THEN** no line of `events.jsonl` holds `secret text`, `other text` or `why text`

#### Scenario: AC-CLI-017.4 A refused command

- **GIVEN** a project with `telemetry.langfuse: true`
- **WHEN** `phase nowhere --change <ref>` is refused
- **THEN** the change's `events.jsonl` is unchanged

#### Scenario: AC-CLI-017.5 Telemetry off

- **GIVEN** a project with no `telemetry` block
- **WHEN** `new`, `gate` and `commit` run
- **THEN** no change folder holds `events.jsonl`

### Requirement: REQ-CLI-018 telemetry push

`specworks telemetry push --change <ref>` SHALL send the change's unsent
events (REQ-INTEG-009), the active change of that name or, when there is none,
the newest archived one, and print how many were sent and how many are still
queued; under `--json` as `sent`, `queued` and `reason` (null when all were
sent). It SHALL exit 1 when events are still queued after it. With telemetry
`off` or `keys missing`, it SHALL be refused naming the reason, and send
nothing.

#### Scenario: AC-CLI-018.1 Sent

- **GIVEN** telemetry `on` with a server that accepts every batch, and a change with 3 unsent events
- **WHEN** `telemetry push --change <ref> --json` runs
- **THEN** it exits 0 with `sent` 3, `queued` 0 and `reason` null

#### Scenario: AC-CLI-018.2 Still queued

- **GIVEN** telemetry `on` with a server that answers 500, and a change with 3 unsent events
- **WHEN** `telemetry push --change <ref> --json` runs
- **THEN** it exits 1 with `sent` 0, `queued` 3 and a reason naming the status

#### Scenario: AC-CLI-018.3 Not configured

- **WHEN** `telemetry push --change <ref> --json` runs with telemetry `off`, or opted in without `SPECWORKS_LANGFUSE_SECRET_KEY`
- **THEN** it prints `{"error": …}` saying telemetry is off, or naming the missing key, exits 1, and makes no request

### Requirement: REQ-CLI-019 A change's telemetry IDs

`status --json` SHALL show, for an active or archived change, `telemetry`
with its `traceId` and `sessionId` (REQ-PROJ-031), whether or not telemetry
is opted in.

#### Scenario: AC-CLI-019.1 The IDs

- **GIVEN** a change `add-login`
- **WHEN** `status --change add-login --json` runs, before and after it is archived
- **THEN** both show `telemetry` with the same `traceId` and `sessionId` `add-login`

## MODIFIED Requirements

### Requirement: REQ-CLI-004 Overview commands

`context` SHALL show the workspace: root, current module, inherited context,
commands, modules (and missing ones) each with its docs folder (`docsPath`)
and whether it holds `architecture.md` (`hasArchitecture`), every capability with its docs path,
test folder (`testsPath`), prefix and delta path, the changes, the skills state (`skills`: `current`,
`outdated` with its files, or `none`), and the telemetry state (`telemetry`:
`state` `on`, `keys missing` or `off`, and the `host`; never a key). When the skills are outdated, it SHALL
also show the hint `skills out of date: run specworks update`. `list` SHALL
list the current module's active changes (every module's with `--all`,
archived ones with `--archived`), flagging an active change that also has an
archived copy. `module list` SHALL show every module with the current one
marked.

#### Scenario: AC-CLI-004.1 Context

- **WHEN** `context` runs
- **THEN** each capability shows its docs path, its test folder (`testsPath`, relative to the workspace root, whether or not it exists) and whether it has a living spec

#### Scenario: AC-CLI-004.2 All modules

- **WHEN** `list` runs with and without `--all`
- **THEN** it lists the current module's changes, or every module's

#### Scenario: AC-CLI-004.3 Archived and leftover changes

- **WHEN** `list --archived` runs, or an active change has an archived copy
- **THEN** archived changes are listed with their date and state, and the leftover copy is flagged with `alsoArchived`

#### Scenario: AC-CLI-004.4 Module tree

- **WHEN** `module list` runs
- **THEN** it lists `(top)` and every module, the current one marked

#### Scenario: AC-CLI-004.5 Skills state

- **GIVEN** installed skills where one skill file was edited
- **WHEN** `context` runs, with and without `--json`
- **THEN** the JSON has `skills` with state `outdated` and that file, and the text output shows `skills out of date: run specworks update`; with current skills, the JSON state is `current` and there is no hint

#### Scenario: AC-CLI-004.6 Each module's docs folder

- **GIVEN** a top level with `docs/architecture.md` and module `billing` at `services/billing` without one
- **WHEN** `context --json` runs
- **THEN** the `(top)` entry of `modules` has `docsPath` `docs` and `hasArchitecture` true, and `billing`'s has `docsPath` `services/billing/docs` and `hasArchitecture` false

#### Scenario: AC-CLI-004.7 Telemetry state

- **GIVEN** a config with `telemetry.langfuse: true` and keys `pk-test` and `sk-test` set in the environment
- **WHEN** `context --json` runs, then again with `SPECWORKS_LANGFUSE_SECRET_KEY` unset, then with no `telemetry` block
- **THEN** `telemetry.state` is `on`, `keys missing`, then `off`, the host is `https://cloud.langfuse.com`, and the output never holds `pk-test` or `sk-test`

### Requirement: REQ-CLI-012 commit

`specworks commit --change <ref>` SHALL commit the change's phase
(REQ-PROJ-024), the active change of that name or, when there is none, the
newest archived one, with `--message` for the subject, `--trailer` (repeatable)
for the trailers and `--json`. It SHALL print the commit's short hash and
subject, the files committed, and the files left out, each relative to the
workspace root; under `--json` it SHALL return them as `commit` (null when
nothing was committed), `committed`, `leftOut` and `alreadyDirty`. With
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

### Requirement: REQ-CLI-013 config set

`config set <key> [<value>]` SHALL set the key in the config of the current
module, or of the module `--module` names (`branch_per_change` and
`telemetry.*` always in the top level's config, which is the only one read for them), and print the key and the config's
path. The value SHALL come from the argument, or from the file `--file`
names (`-` reads standard input); giving both, or neither, SHALL be refused
before writing. An error SHALL leave the config unchanged.

#### Scenario: AC-CLI-013.1 Setting a command

- **WHEN** `config set commands.test "uv run pytest" --json` runs
- **THEN** it prints the key, the value and the config's path relative to the workspace root, and `specworks context` shows that test command

#### Scenario: AC-CLI-013.2 The context from a file or standard input

- **WHEN** `config set context --file notes.txt` runs, or `config set context --file -` with the text on standard input
- **THEN** the context is that text

#### Scenario: AC-CLI-013.3 Both a value and a file, or neither

- **WHEN** `config set context "text" --file notes.txt` or `config set context` runs
- **THEN** it is refused and the config is unchanged

#### Scenario: AC-CLI-013.4 In a module

- **GIVEN** module `billing`
- **WHEN** `config set commands.test "go test ./..." --module billing` runs from the top level
- **THEN** billing's config has that test command and the top level's config is unchanged

#### Scenario: AC-CLI-013.5 A refused key under --json

- **WHEN** `config set commands.unit pytest --json` runs
- **THEN** it prints `{"error": ...}`, exits 1, and the config is unchanged

#### Scenario: AC-CLI-013.6 The branch setting from inside a module

- **GIVEN** module `billing`
- **WHEN** `config set branch_per_change false --json` runs inside `billing`'s folder, or with `--module billing`
- **THEN** the top level's config has `branch_per_change: false`, billing's config is unchanged, and the output names the top level's config

#### Scenario: AC-CLI-013.7 Telemetry from inside a module

- **GIVEN** module `billing`
- **WHEN** `config set telemetry.langfuse true --json` runs inside `billing`'s folder
- **THEN** the top level's config has `telemetry.langfuse: true`, billing's config is unchanged, and the output names the top level's config
