# Spec Delta: project

## ADDED Requirements

### Requirement: REQ-PROJ-017 The git repository

The system SHALL require the folder of a new project, or of a new change, to be
inside a git repository, and SHALL refuse it otherwise with an error that says
to run `git init`. A missing git installation SHALL be refused the same way,
naming the failure. The system SHALL NOT create a repository itself.

#### Scenario: AC-PROJ-017.1 A folder in a repository

- **WHEN** the check runs in a folder of a git repository, at its root or in a sub-folder
- **THEN** it passes

#### Scenario: AC-PROJ-017.2 A folder outside a repository

- **WHEN** the check runs in a folder that is in no git repository
- **THEN** it is refused with an error naming `git init`, and no repository is created

#### Scenario: AC-PROJ-017.3 Git is not installed

- **WHEN** the check runs and the `git` program cannot be run
- **THEN** it is refused with an error saying git cannot be run

### Requirement: REQ-PROJ-018 A change's branch

The system SHALL name a change's branch after its ref with the `:` between
module and name replaced by `/`: `<name>` for a change of the top level,
`<module>/<name>` for a change of a module (`<parent>/<child>/<name>` for a
nested one). It SHALL create that branch and switch to it, and SHALL refuse a
branch of that name that already exists, naming it.

#### Scenario: AC-PROJ-018.1 A change of the top level

- **WHEN** the branch of change `add-login` is created
- **THEN** the branch `add-login` exists and is checked out

#### Scenario: AC-PROJ-018.2 A change of a module

- **WHEN** the branch of change `add-login` of module `billing` (or of nested module `billing/tax`) is created
- **THEN** the branch is `billing/add-login` (or `billing/tax/add-login`)

#### Scenario: AC-PROJ-018.3 The branch already exists

- **GIVEN** a branch named like the change
- **WHEN** its branch is created
- **THEN** it is refused naming the branch, and the checked-out branch is unchanged

### Requirement: REQ-PROJ-019 Where a change's branch starts

A change's branch SHALL start at the current HEAD, with the uncommitted changes
of the working tree carried over untouched. The system SHALL refuse a detached
HEAD, saying to switch to a branch first, and SHALL report the branch it
started from when that is not the base branch. A repository without commits
SHALL still get the branch.

#### Scenario: AC-PROJ-019.1 From the current HEAD

- **GIVEN** HEAD on `main` with a modified and an untracked file
- **WHEN** the change's branch is created
- **THEN** the branch points at the commit `main` pointed at, and both files are still modified and untracked

#### Scenario: AC-PROJ-019.2 A detached HEAD

- **WHEN** the branch is created with a detached HEAD
- **THEN** it is refused saying to switch to a branch first, and no branch is created

#### Scenario: AC-PROJ-019.3 Not on the base branch

- **GIVEN** HEAD on a branch other than the base branch (found as review finds it)
- **WHEN** the change's branch is created
- **THEN** the result names that branch as the one it started from; on the base branch, or when the base branch is not found, it names none

#### Scenario: AC-PROJ-019.4 No commits yet

- **GIVEN** a repository with no commit
- **WHEN** the change's branch is created
- **THEN** the branch exists and is checked out
