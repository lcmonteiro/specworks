# Spec Delta: project

## ADDED Requirements

### Requirement: REQ-PROJ-035 Setting the harness model

The system SHALL set `harness.model` (a model id) in a project's config,
editing it as text and keeping the user's comments and other entries: one
line under `harness:`, replacing that key's line when there is one, and a
`harness:` entry added when there is none. An empty value SHALL clear it.

#### Scenario: AC-PROJ-035.1 The model set with the comments kept

- **GIVEN** the default config written by `init`
- **WHEN** `harness.model` is set to `gpt-4.1`
- **THEN** the config loads with that harness model, has one `harness:` entry with one `model:` line, and its comments are still there

#### Scenario: AC-PROJ-035.2 Replaced and cleared

- **GIVEN** a config whose `harness.model` is `gpt-4.1`
- **WHEN** `harness.model` is set to `claude-sonnet-4`, then to an empty value
- **THEN** the config first loads with `claude-sonnet-4` and one `model:` line, then with no harness model

#### Scenario: AC-PROJ-035.3 A model id with YAML characters

- **WHEN** `harness.model` is set to `org/model: v2 # beta`
- **THEN** the config loads with exactly that harness model

## MODIFIED Requirements

### Requirement: REQ-PROJ-003 Config value checks

The system SHALL reject a config whose values have the wrong shape, with an
error naming the setting: paths that leave the project, globs that are not a
list of `*`/`?`/`**` patterns, a context that is not text or is larger than
51200 bytes, commands that are not a mapping of test, test_scoped, lint,
typecheck, build or format to a command string, a `test_scoped` command
without the `{paths}` placeholder, diagram settings that are not a known theme, a
known layout (elk or dagre), a true/false sketch and a non-negative pad,
`tools` that is not a non-empty list of known tool IDs or is set in a module's
config, `telemetry` that is not a mapping of `langfuse` (true or false)
and `host` (an `http://` or `https://` URL) or is set in a module's config,
and `harness` that is not a mapping of `model` (a non-empty string) or is set
in a module's config.

#### Scenario: AC-PROJ-003.1 Paths stay inside the project

- **WHEN** `docs_dir`, `tests_dir`, a capability path, a capability's `tests` or a module path is absolute, contains `..` or is not a non-empty string
- **THEN** loading (or adding the entry) fails saying it must be a relative folder inside the project

#### Scenario: AC-PROJ-003.2 Globs

- **WHEN** `test_globs` or `source_globs` is a single string, holds a non-string, or uses `[..]` or `{..}`
- **THEN** loading fails with a message naming the key (for a single string, showing it as a list)

#### Scenario: AC-PROJ-003.3 Context

- **WHEN** `context` is not a string, or is larger than 51200 bytes
- **THEN** loading fails saying so

#### Scenario: AC-PROJ-003.4 Commands

- **WHEN** `commands` is not a mapping, or a command is not a string
- **THEN** loading fails naming `commands` (with the allowed keys) or `commands.<key>`

#### Scenario: AC-PROJ-003.5 Diagram settings

- **WHEN** `diagrams.theme` or `diagrams.dark_theme` is not a known theme, or `diagrams.pad` is not a non-negative number
- **THEN** loading fails naming the setting; `dark_theme: none` is accepted and means the light theme is used in dark mode too

#### Scenario: AC-PROJ-003.6 Tools

- **WHEN** `tools` is not a list, is empty, or holds an unknown tool (e.g. `cursor`)
- **THEN** loading fails naming `tools` and the known tool IDs

#### Scenario: AC-PROJ-003.7 Tools in a module

- **WHEN** a module's config sets `tools`
- **THEN** loading fails saying `tools` is set in the top level's config

#### Scenario: AC-PROJ-003.8 A scoped test command without its placeholder

- **WHEN** `commands.test_scoped` is `uv run pytest`, with no `{paths}`
- **THEN** loading fails naming `commands.test_scoped` and saying it must hold `{paths}`; `uv run pytest {paths}` loads

#### Scenario: AC-PROJ-003.9 Telemetry

- **WHEN** `telemetry` is not a mapping, has a key other than `langfuse` and `host`, `telemetry.langfuse` is not true or false, or `telemetry.host` is `cloud.langfuse.com` (no scheme)
- **THEN** loading fails naming `telemetry` or the setting; `{langfuse: true, host: "http://localhost:3000"}` loads

#### Scenario: AC-PROJ-003.10 Telemetry in a module

- **WHEN** a module's config sets `telemetry`
- **THEN** loading fails saying `telemetry` is set in the top level's config

#### Scenario: AC-PROJ-003.11 Harness settings

- **WHEN** `harness` is not a mapping, has a key other than `model`, or `harness.model` is not a string or is empty
- **THEN** loading fails naming `harness` or `harness.model`; `{model: gpt-4.1}` loads and gives that model

#### Scenario: AC-PROJ-003.12 Harness settings in a module

- **WHEN** a module's config sets `harness`
- **THEN** loading fails saying `harness` is set in the top level's config

### Requirement: REQ-PROJ-025 Setting a command, the context or the branch setting

The system SHALL set `commands.<key>` (a key of `test`, `test_scoped`, `lint`, `typecheck`,
`build`, `format`) or `context` in a project's config, editing it as text:
the user's comments and the other entries SHALL be kept. A command SHALL be
one line under `commands:`, replacing that key's line when there is one; the
context SHALL be a block replacing the `context:` entry there. An empty value
SHALL clear the key. `branch_per_change` SHALL take `true` or `false` and be
one top-level line, replacing the one there. The telemetry settings are set as
REQ-PROJ-032 says, and the harness model as REQ-PROJ-035 says. Any other key SHALL be refused before writing, naming the
keys it accepts. A context larger than the config's size limit SHALL be
refused before writing, naming the limit. A `test_scoped` command without `{paths}` SHALL be
refused before writing, saying it must hold `{paths}`. When the edit would not load with the new value and every
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

- **WHEN** `commands.unit`, `docs_dir`, `telemetry.secret_key` or `harness.api_key` is set
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

#### Scenario: AC-PROJ-025.13 The scoped test command

- **GIVEN** the default config written by `init`
- **WHEN** `commands.test_scoped` is set to `uv run pytest {paths}`, then to `uv run pytest`
- **THEN** the config loads with that scoped test command and one `test_scoped:` line, and `uv run pytest` is refused saying it must hold `{paths}`, the file unchanged
