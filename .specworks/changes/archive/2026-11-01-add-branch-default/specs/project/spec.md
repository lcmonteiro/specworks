# Spec Delta: project

## ADDED Requirements

### Requirement: REQ-PROJ-026 The branch setting

The config SHALL accept a top-level `branch_per_change`, `true` or `false`,
saying whether a new change gets its own branch; it SHALL default to `true`
when absent. Any other value SHALL be refused when the config loads, naming
the key. The workspace SHALL use the top level's value; a module's own
`branch_per_change` SHALL be ignored. The default config written by `init`
SHALL describe the key without setting it.

#### Scenario: AC-PROJ-026.1 The default

- **GIVEN** a config with no `branch_per_change`, or the default config written by `init`
- **WHEN** it loads
- **THEN** `branch_per_change` is true, and the default config's text names `branch_per_change`

#### Scenario: AC-PROJ-026.2 Set to false

- **GIVEN** a config with `branch_per_change: false`
- **WHEN** it loads
- **THEN** `branch_per_change` is false

#### Scenario: AC-PROJ-026.3 A value that is not true or false

- **GIVEN** a config with `branch_per_change: sometimes`
- **WHEN** it loads
- **THEN** it is refused with an error naming `branch_per_change`

#### Scenario: AC-PROJ-026.4 A module's own value

- **GIVEN** a top level with `branch_per_change: false` and module `billing` with `branch_per_change: true`
- **WHEN** the workspace's setting is read from inside `billing`
- **THEN** it is false

## MODIFIED Requirements

### Requirement: REQ-PROJ-025 Setting a command, the context or the branch setting

The system SHALL set `commands.<key>` (a key of `test`, `lint`, `typecheck`,
`build`, `format`) or `context` in a project's config, editing it as text:
the user's comments and the other entries SHALL be kept. A command SHALL be
one line under `commands:`, replacing that key's line when there is one; the
context SHALL be a block replacing the `context:` entry there. An empty value
SHALL clear the key. `branch_per_change` SHALL take `true` or `false` and be
one top-level line, replacing the one there. Any other key SHALL be refused before writing, naming the
keys it accepts. A context larger than the config's size limit SHALL be
refused before writing, naming the limit. When the edit would not load with the new value and every
other entry unchanged, the file SHALL be left unchanged and the error SHALL
say to set the key by hand.

#### Scenario: AC-PROJ-025.1 A command set with the comments kept

- **GIVEN** the default config written by `init`
- **WHEN** `commands.test` is set to `uv run pytest`
- **THEN** the config loads with that test command, its comments are still there, and it has one `test:` line

#### Scenario: AC-PROJ-025.2 A command replaced

- **GIVEN** a config whose `commands.lint` is `ruff check .`
- **WHEN** `commands.lint` is set to `uv run ruff check src`
- **THEN** the config loads with the new lint command, has one `lint:` line, and its other commands are unchanged

#### Scenario: AC-PROJ-025.3 A command added to a config without commands

- **GIVEN** a config with no `commands:` entry
- **WHEN** `commands.build` is set to `make`
- **THEN** the config loads with that build command

#### Scenario: AC-PROJ-025.4 A command with YAML characters

- **WHEN** `commands.test` is set to `pytest -k "a or b" # all: yes`
- **THEN** the config loads with exactly that test command

#### Scenario: AC-PROJ-025.5 A command cleared

- **GIVEN** a config whose `commands.lint` is `ruff check .`
- **WHEN** `commands.lint` is set to an empty value
- **THEN** the config loads with no lint command and its other commands unchanged

#### Scenario: AC-PROJ-025.6 The context set

- **GIVEN** the default config written by `init`
- **WHEN** `context` is set to a text of three lines
- **THEN** the config loads with exactly that text as its context, and the entries after `context:` are unchanged

#### Scenario: AC-PROJ-025.7 The context replaced

- **GIVEN** a config whose context is a block of two lines
- **WHEN** `context` is set to another text
- **THEN** the config loads with the new text only and has one `context:` entry

#### Scenario: AC-PROJ-025.8 An unknown key

- **WHEN** `commands.unit` or `docs_dir` is set
- **THEN** it is refused naming the keys it accepts, and the config file is unchanged

#### Scenario: AC-PROJ-025.9 An entry the text edit cannot change

- **GIVEN** a config with `commands: {test: pytest}`
- **WHEN** `commands.lint` is set to `ruff check .`
- **THEN** the config file is unchanged and the error says to set `commands.lint` by hand

#### Scenario: AC-PROJ-025.10 A command added to the commands block

- **GIVEN** the default config written by `init`
- **WHEN** `commands.typecheck` is set to `uv run mypy`
- **THEN** the config loads with that typecheck command and its test and lint entries unchanged, has one `typecheck:` line, and its comments are still there

#### Scenario: AC-PROJ-025.11 A context over the size limit

- **WHEN** `context` is set to a text larger than the config's size limit
- **THEN** it is refused naming the limit, and the config file is unchanged

#### Scenario: AC-PROJ-025.12 The branch setting

- **GIVEN** the default config written by `init`
- **WHEN** `branch_per_change` is set to `false`, then to `maybe`
- **THEN** the config loads with `branch_per_change` false and one `branch_per_change:` line, and `maybe` is refused naming `true` and `false`, the file unchanged

