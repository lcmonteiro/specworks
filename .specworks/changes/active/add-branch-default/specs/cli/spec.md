# Spec Delta: cli

## ADDED Requirements

### Requirement: REQ-CLI-015 Staying on the branch

`new` SHALL create the change's branch when the workspace's
`branch_per_change` is true and stay on the current branch when it is false;
`--branch` SHALL create it and `--no-branch` SHALL stay, whatever the
setting. When it stays, the output SHALL name the branch it stayed on (none
with a detached HEAD), and `branch` SHALL be
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

## MODIFIED Requirements

### Requirement: REQ-CLI-006 Creating, moving and dropping changes

`new` SHALL create a change in the module nearest the working directory, or in
`--module`, and put it on its own branch: it creates and switches to the
change's branch unless `branch_per_change` or `--no-branch` says to stay
(REQ-CLI-015), and it SHALL fail without
creating the change, naming the reason, when the folder is not inside a git
repository, the branch already exists, or HEAD is detached. `phase <phase>
--change <ref>` SHALL move a change without checking gates, and SHALL refuse
the old argument order with a hint. `abandon` SHALL archive a change without
merging, and requires a reason. `skip-specs` SHALL mark a change as having no
behaviour change, and `--off` removes the mark.

#### Scenario: AC-CLI-006.1 Where a change is created

- **WHEN** `new` runs inside a module's folder, or with `--module`
- **THEN** the change is created in that module; an unknown module is refused

#### Scenario: AC-CLI-006.2 Moving a change

- **WHEN** `phase` names a phase, or an unknown one
- **THEN** the change moves, or the command fails

#### Scenario: AC-CLI-006.3 The change comes with --change

- **WHEN** `phase` is called without `--change` or in the old order
- **THEN** it fails with the corrected command as a hint

#### Scenario: AC-CLI-006.4 Abandoning

- **WHEN** a change is abandoned with a reason
- **THEN** it is archived with its phase and reason, the living spec is untouched, and it leaves the active list; a blank reason is refused

#### Scenario: AC-CLI-006.5 No behaviour change

- **WHEN** `skip-specs` runs, then `skip-specs --off`
- **THEN** the specs artifact is skipped, then required again

#### Scenario: AC-CLI-006.6 The change's branch

- **WHEN** `new` creates a change
- **THEN** the checked-out branch is the change's branch, and the output (and `--json` as `branch`) names it

#### Scenario: AC-CLI-006.7 Staying on the current branch

- **WHEN** `new --no-branch` creates a change
- **THEN** the checked-out branch is unchanged, and `--json` has `branch` null

#### Scenario: AC-CLI-006.8 Nothing is left behind

- **WHEN** `new` runs outside a git repository, with the change's branch already existing, or with a detached HEAD
- **THEN** it fails naming the reason, and no change folder and no branch are created

#### Scenario: AC-CLI-006.9 Not on the base branch

- **WHEN** `new` runs on a branch other than the base branch
- **THEN** the output (and `--json` as `startedFrom`) names that branch; on the base branch it says nothing

### Requirement: REQ-CLI-013 config set

`config set <key> [<value>]` SHALL set the key in the config of the current
module, or of the module `--module` names (`branch_per_change` always in the
top level's config, which is the only one read for it), and print the key and the config's
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

