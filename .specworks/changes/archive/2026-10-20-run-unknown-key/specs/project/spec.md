# Spec Delta: project

## MODIFIED Requirements

### Requirement: REQ-PROJ-013 Running the project's commands

The system SHALL run a configured command (`commands.<key>`, merged from the
top level down to the module) through the shell in the module's folder, and
report its exit code and output. A key that is not a command key (`test`,
`lint`, `typecheck`, `build`, `format`) SHALL be an error listing the valid
keys. A command key that is not configured SHALL be an error saying where to
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
- **THEN** it fails with `unknown command 'frobnicate'` listing `test, lint, typecheck, build, format`, and doesn't suggest adding it to the config
