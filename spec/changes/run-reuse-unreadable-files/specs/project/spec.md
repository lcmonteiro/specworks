# Spec Delta: project

## MODIFIED Requirements

### Requirement: REQ-PROJ-014 Reusing command results

The system SHALL reuse the result of a command run on an identical working tree
(same command and folder, same `HEAD`, same uncommitted changes, same untracked
files and contents, the workflow folders left out), passing or failing. Every
real run SHALL replace the recorded result for its tree. Reuse SHALL be off
without git, when `SPECWORKS_RUN_CACHE=0`, when a git submodule holds untracked
files, and when an untracked file cannot be read. An untracked file's name SHALL
count as the bytes git reports, whatever its encoding.

#### Scenario: AC-PROJ-014.1 Same tree

- **WHEN** a gate runs the same command twice on the same tree
- **THEN** the command runs once and the second result says `same code as the run at ...`

#### Scenario: AC-PROJ-014.2 What changes the tree

- **WHEN** only a workflow file changes
- **THEN** the result is reused; a changed tracked file, a new untracked file or new content in it runs the command again

#### Scenario: AC-PROJ-014.3 A failure is reused too

- **WHEN** the command failed on this tree
- **THEN** the failure is reused with its exit code

#### Scenario: AC-PROJ-014.4 Reuse turned off

- **WHEN** `SPECWORKS_RUN_CACHE=0` is set, or the project is not in a git repository
- **THEN** every run is real

#### Scenario: AC-PROJ-014.5 An explicit run

- **WHEN** a command is run with `specworks run`
- **THEN** it always runs, and its result replaces the one later gates reuse, passing or failing

#### Scenario: AC-PROJ-014.6 Git submodules

- **WHEN** a submodule's tracked files change
- **THEN** the command runs again; while it holds untracked files, no result is reused

#### Scenario: AC-PROJ-014.7 A file name that is not UTF-8

- **GIVEN** an untracked file whose name is not valid UTF-8 (e.g. `caf\xe9.py`)
- **WHEN** a gate runs the same command twice on the same tree
- **THEN** nothing crashes, the command runs once, and the second result is reused

#### Scenario: AC-PROJ-014.8 An untracked file that cannot be read

- **GIVEN** an untracked file the fingerprint cannot read
- **WHEN** a gate runs the command, twice
- **THEN** nothing crashes, and the command runs for real both times
