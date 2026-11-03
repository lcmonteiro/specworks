## ADDED Requirements

### Requirement: REQ-PROJ-027 A capability's test folder

The system SHALL give each capability a test folder: the capability's `tests`
when set, otherwise `<tests_dir>/<capability name>`, where `tests_dir` is a
setting of the capability's own module (default `tests`); either is relative
to that module's folder. A capability's test folder SHALL be known whether or
not the folder exists.

#### Scenario: AC-PROJ-027.1 The default test folder

- **GIVEN** a config with no `tests_dir` and a capability `auth` with no `tests`
- **WHEN** the workspace is loaded
- **THEN** the test folder of `auth` is `tests/auth`

#### Scenario: AC-PROJ-027.2 The module's tests_dir

- **GIVEN** a config with `tests_dir: test` and a capability `auth`
- **WHEN** the workspace is loaded
- **THEN** the test folder of `auth` is `test/auth`

#### Scenario: AC-PROJ-027.3 A capability's own tests folder

- **GIVEN** a capability `auth` with `tests: src/auth`
- **WHEN** the workspace is loaded
- **THEN** its test folder is `src/auth`, whatever `tests_dir` is

#### Scenario: AC-PROJ-027.4 Inside a module

- **GIVEN** module `billing` at `services/billing` with `tests_dir: spec` and a capability `invoices`, and a top level with `tests_dir: tests`
- **WHEN** the workspace is loaded
- **THEN** the test folder of `billing:invoices` is `services/billing/spec/invoices`

### Requirement: REQ-PROJ-028 Running the scoped tests

The system SHALL run a module's `test_scoped` command for a list of test
folders by replacing every `{paths}` in it with those folders, relative to the
module's folder, each quoted for the shell and separated by spaces, then
running it as a command of that module (in its folder, its result reused on an
identical tree like any command's). A result SHALL be reused only for the same
folders.

#### Scenario: AC-PROJ-028.1 The folders filled in

- **GIVEN** `commands.test_scoped` is `uv run pytest {paths}`
- **WHEN** it runs for `tests/auth` and `tests/my tests`
- **THEN** the command run is `uv run pytest tests/auth 'tests/my tests'` (quoted for the platform's shell), in the module's folder, and its exit code and output are reported

#### Scenario: AC-PROJ-028.2 In a module

- **GIVEN** module `billing` at `services/billing` with `tests_dir: spec` and `commands.test_scoped` set
- **WHEN** it runs for the test folder of `billing:invoices`
- **THEN** it runs in `services/billing` with `spec/invoices` (relative to the module), not the workspace path

#### Scenario: AC-PROJ-028.3 Reused only for the same folders

- **WHEN** the scoped tests run for `tests/auth` and then, on the same tree, for `tests/auth` and `tests/billing`
- **THEN** the second run is real; running again for `tests/auth` and `tests/billing` reuses it

## MODIFIED Requirements

### Requirement: REQ-PROJ-003 Config value checks

The system SHALL reject a config whose values have the wrong shape, with an
error naming the setting: paths that leave the project, globs that are not a
list of `*`/`?`/`**` patterns, a context that is not text or is larger than
51200 bytes, commands that are not a mapping of test, test_scoped, lint,
typecheck, build or format to a command string, a `test_scoped` command
without the `{paths}` placeholder, diagram settings that are not a known theme, a
known layout (elk or dagre), a true/false sketch and a non-negative pad, and
`tools` that is not a non-empty list of known tool IDs or is set in a module's
config.

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

### Requirement: REQ-PROJ-004 Capabilities in the config

The system SHALL read each capability as a kebab-case name with a code path,
given either as `name: path` or as a mapping with `path`, an optional
`prefix`, an optional `description` and an optional `tests` (its test folder), and SHALL derive its requirement ID
prefix, when none is given, from its module path and name in upper case.

#### Scenario: AC-PROJ-004.1 Name and path only

- **WHEN** a capability is given as `user-auth: src/auth/`
- **THEN** its path is `src/auth` and its prefix is `USER-AUTH`

#### Scenario: AC-PROJ-004.2 Prefix inside a module

- **GIVEN** a capability `invoices` in module `billing`, with no `prefix`
- **WHEN** the workspace is loaded
- **THEN** its prefix is `BILLING-INVOICES`

#### Scenario: AC-PROJ-004.3 Empty description

- **WHEN** a capability's `description:` is empty
- **THEN** its description is the empty string

#### Scenario: AC-PROJ-004.4 Name must be kebab-case

- **WHEN** a capability name is not kebab-case (e.g. `Bad_Name`)
- **THEN** it is rejected with a message saying it must be kebab-case

### Requirement: REQ-PROJ-013 Running the project's commands

The system SHALL run a configured command (`commands.<key>`, merged from the
top level down to the module) through the shell in the module's folder, and
report its exit code and output. A key that is not a command key (`test`,
`test_scoped`, `lint`, `typecheck`, `build`, `format`) SHALL be an error listing the valid
keys. Running `test_scoped` directly SHALL be an error saying the review gate
fills its `{paths}`, without running anything. A command key that is not configured SHALL be an error saying where to
add it, with an example for that key.

#### Scenario: AC-PROJ-013.1 Exit code and output

- **WHEN** a configured command runs
- **THEN** its exit code and the tail of its output are reported

#### Scenario: AC-PROJ-013.2 In the module's folder

- **WHEN** a module's command runs
- **THEN** it runs in that module's folder

#### Scenario: AC-PROJ-013.3 Not configured

- **WHEN** a command that is not configured is run
- **THEN** it fails with `no '<key>' command configured`, the config to add it to, and an example for that key (`lint: <command>`)

#### Scenario: AC-PROJ-013.4 Not a command key

- **WHEN** a key that is not a command key, such as `frobnicate`, is run
- **THEN** it fails with `unknown command 'frobnicate'` listing `test, test_scoped, lint, typecheck, build, format`, and doesn't suggest adding it to the config

#### Scenario: AC-PROJ-013.5 The scoped test command run directly

- **GIVEN** `commands.test_scoped` is `uv run pytest {paths}`
- **WHEN** `specworks run test_scoped` runs
- **THEN** it fails saying the review gate fills `{paths}` (and to run `test` for the whole suite), and no command runs

### Requirement: REQ-PROJ-025 Setting a command, the context or the branch setting

The system SHALL set `commands.<key>` (a key of `test`, `test_scoped`, `lint`, `typecheck`,
`build`, `format`) or `context` in a project's config, editing it as text:
the user's comments and the other entries SHALL be kept. A command SHALL be
one line under `commands:`, replacing that key's line when there is one; the
context SHALL be a block replacing the `context:` entry there. An empty value
SHALL clear the key. `branch_per_change` SHALL take `true` or `false` and be
one top-level line, replacing the one there. Any other key SHALL be refused before writing, naming the
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

#### Scenario: AC-PROJ-025.13 The scoped test command

- **GIVEN** the default config written by `init`
- **WHEN** `commands.test_scoped` is set to `uv run pytest {paths}`, then to `uv run pytest`
- **THEN** the config loads with that scoped test command and one `test_scoped:` line, and `uv run pytest` is refused saying it must hold `{paths}`, the file unchanged

