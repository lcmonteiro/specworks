## ADDED Requirements

### Requirement: REQ-CLI-010 merge

`specworks merge <branch> --change <ref>` SHALL merge the branch for the change
and print whether it merged and which files it resolved; with `--json` it SHALL
print `merged`, `branch` and `resolved`. A failure SHALL be an error value
(`{"error": ...}` under `--json`) with exit code 1, and a folder outside a git
repository SHALL be refused saying so.

#### Scenario: AC-CLI-010.1 A merged branch

- **WHEN** `merge <branch> --change <ref> --json` merges with `tasks.md` resolved
- **THEN** it exits 0 and prints `merged: true`, the branch and `resolved: [<path to tasks.md>]`, the path relative to the workspace root

#### Scenario: AC-CLI-010.2 A refused merge

- **WHEN** the merge is aborted on another conflict
- **THEN** it exits 1 with an error naming the conflicting files

#### Scenario: AC-CLI-010.3 Outside git

- **WHEN** the project is not in a git repository
- **THEN** it exits 1 with an error saying it needs a git repository, and nothing changes
