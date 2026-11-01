# Spec Delta: cli

## ADDED Requirements

### Requirement: REQ-CLI-012 commit

`specworks commit --change <ref>` SHALL commit the change's phase
(REQ-PROJ-024), with `--message` for the subject, `--trailer` (repeatable)
for the trailers and `--json`. It SHALL print the commit's short hash and
subject, the files committed, and the files left out, each relative to the
workspace root; under `--json` it SHALL return them as `commit` (null when
nothing was committed), `committed`, `leftOut` and `alreadyDirty`. A refusal
SHALL be an error (`{"error": …}` with exit 1 under `--json`).

#### Scenario: AC-CLI-012.1 A commit

- **WHEN** `commit --change add-login --trailer "Co-Authored-By: A <a@x>" --json` runs with phase files changed
- **THEN** it exits 0 and returns the commit, the committed and left-out paths relative to the workspace root, and `git log` shows the subject and trailer

#### Scenario: AC-CLI-012.2 Nothing to commit

- **WHEN** `commit --change add-login --json` runs with nothing changed since the record
- **THEN** it exits 0 with `commit` null and an empty `committed`

#### Scenario: AC-CLI-012.3 An unknown change

- **WHEN** `commit --change nope --json` runs
- **THEN** it prints `{"error": …}` naming `nope` and exits 1
