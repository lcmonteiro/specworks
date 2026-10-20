# Spec Delta: cli

## MODIFIED Requirements

### Requirement: REQ-CLI-008 diagrams

`diagrams` SHALL render the diagrams of a change (`--change`) or of a folder
inside the workspace (`--dir`), or list the themes (`--themes`) with the ones in
use and the d2 found. It requires one of these. `--check` SHALL only report the
diagrams' states and exit 1 when any is missing or stale. A relative `--dir` SHALL be
resolved from the workspace root, wherever the command runs. A folder outside
the workspace, or one that doesn't exist, SHALL be refused.

#### Scenario: AC-CLI-008.1 What to render

- **WHEN** `diagrams` runs with none of `--change`, `--dir` or `--themes`
- **THEN** it fails asking for `--change`

#### Scenario: AC-CLI-008.2 Themes

- **WHEN** `diagrams --themes` runs
- **THEN** it lists every theme with its number and whether it is dark, and the theme and dark theme in use

#### Scenario: AC-CLI-008.3 Check only

- **WHEN** `diagrams --check` runs and a diagram is stale
- **THEN** it exits 1 without rendering

#### Scenario: AC-CLI-008.4 A docs folder

- **WHEN** `diagrams --dir src/auth/docs` runs
- **THEN** that folder's diagrams are rendered and the folder is reported relative to the root

#### Scenario: AC-CLI-008.5 A folder outside the workspace

- **WHEN** `--dir` names a folder outside the workspace
- **THEN** it is refused with `is outside the workspace`

#### Scenario: AC-CLI-008.6 From a subfolder

- **GIVEN** a working directory inside a module of the workspace
- **WHEN** `diagrams --dir src/auth/docs` runs, the folder named relative to the workspace root
- **THEN** that folder's diagrams are rendered

#### Scenario: AC-CLI-008.7 A folder that doesn't exist

- **WHEN** `--dir` names a folder that doesn't exist
- **THEN** it fails with `no folder`, naming the folder relative to the root, and renders nothing
