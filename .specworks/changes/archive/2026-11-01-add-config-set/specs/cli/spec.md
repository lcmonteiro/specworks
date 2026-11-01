# Spec Delta: cli

## ADDED Requirements

### Requirement: REQ-CLI-013 config set

`config set <key> [<value>]` SHALL set the key in the config of the current
module, or of the module `--module` names, and print the key and the config's
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
