# Spec Delta: cli

## MODIFIED Requirements

### Requirement: REQ-CLI-013 config set

`config set <key> [<value>]` SHALL set the key in the config of the current
module, or of the module `--module` names (`branch_per_change`,
`telemetry.*` and `harness.*` always in the top level's config, which is the only one read for them), and print the key and the config's
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

#### Scenario: AC-CLI-013.8 The harness model from inside a module

- **GIVEN** module `billing`
- **WHEN** `config set harness.model gpt-4.1 --json` runs inside `billing`'s folder
- **THEN** the top level's config has `harness.model: gpt-4.1`, billing's config is unchanged, and the output names the top level's config

### Requirement: REQ-CLI-022 harness

`specworks harness`, with no argument or option, SHALL open the harness chat
(REQ-HARNESS-001) in the terminal for the current project, with an empty
conversation, and SHALL say nothing for the user: the user starts or continues
a change by sending a message to a peer, such as `@refine <request>`. Without the `harness` extra,
it SHALL fail saying to install `specworks[harness]`, without naming a Python version. A
model setting missing (REQ-HARNESS-010) SHALL fail before the chat opens: no
model SHALL name `SPECWORKS_MODEL_MODEL` and `harness.model`, and a missing
key with no stored login SHALL say to run `specworks login copilot`. Every failure SHALL be `error: …` on stderr with exit 1. No
other command SHALL import the harness or its dependencies.

#### Scenario: AC-CLI-022.1 Without the extra

- **GIVEN** chatinho or deepagents cannot be imported
- **WHEN** `specworks harness` runs
- **THEN** it exits 1 and stderr says to install `specworks[harness]`, and names no Python version

#### Scenario: AC-CLI-022.2 No key

- **GIVEN** the extra installed, `SPECWORKS_MODEL_API_KEY` unset and no stored login
- **WHEN** `specworks harness` runs
- **THEN** it exits 1 naming `SPECWORKS_MODEL_API_KEY` and saying to run `specworks login copilot`, and no chat opens

#### Scenario: AC-CLI-022.8 No model

- **GIVEN** the extra installed, `SPECWORKS_MODEL_API_KEY` set, `SPECWORKS_MODEL_MODEL` unset and no `harness.model` in the config
- **WHEN** `specworks harness` runs
- **THEN** it exits 1 with `error: …` on stderr naming `SPECWORKS_MODEL_MODEL` and `harness.model`, and no chat opens

#### Scenario: AC-CLI-022.5 Other commands stay light

- **WHEN** `import specworks` and `specworks --help` run without the extra
- **THEN** they succeed, and neither chatinho nor deepagents is imported

#### Scenario: AC-CLI-022.6 The chat opens with nothing said

- **WHEN** `specworks harness` builds its session and starts it
- **THEN** the conversation is empty and no peer runs until the user sends a message, such as `@refine add x`

#### Scenario: AC-CLI-022.7 No change option

- **WHEN** `specworks harness --change add-x` runs
- **THEN** it exits with the command line's usage error naming the unknown option, and no chat opens
