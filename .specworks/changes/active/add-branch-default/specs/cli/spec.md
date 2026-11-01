# Spec Delta: cli

## ADDED Requirements

### Requirement: REQ-CLI-015 Staying on the branch

`new` SHALL create the change's branch when the workspace's
`branch_per_change` is true and stay on the current branch when it is false;
`--branch` SHALL create it and `--no-branch` SHALL stay, whatever the
setting. When it stays, the output SHALL name the branch it stayed on (none
outside a git repository or with a detached HEAD), and `branch` SHALL be
null.

#### Scenario: AC-CLI-015.1 The setting is false

- **GIVEN** `branch_per_change: false` and HEAD on `work`
- **WHEN** `new add-login --json` runs
- **THEN** HEAD is still on `work`, no branch `add-login` exists, and the output has `branch` null and `stayedOn` `work`

#### Scenario: AC-CLI-015.2 --branch overrides false

- **GIVEN** `branch_per_change: false`
- **WHEN** `new add-login --branch` runs
- **THEN** the branch `add-login` is created and checked out

#### Scenario: AC-CLI-015.3 --no-branch overrides true

- **GIVEN** no `branch_per_change` in the config
- **WHEN** `new add-login --no-branch --json` runs
- **THEN** HEAD is still on its branch, and the output has `branch` null and `stayedOn` naming it

#### Scenario: AC-CLI-015.4 No setting, no flag

- **GIVEN** no `branch_per_change` in the config
- **WHEN** `new add-login --json` runs
- **THEN** the branch `add-login` is created and checked out, and `stayedOn` is null

#### Scenario: AC-CLI-015.5 The text output

- **GIVEN** `branch_per_change: false` and HEAD on `work`
- **WHEN** `new add-login` runs
- **THEN** the output has a line `stayed on work`
