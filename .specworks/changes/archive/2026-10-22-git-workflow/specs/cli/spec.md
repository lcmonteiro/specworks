# Spec Delta: cli

## MODIFIED Requirements

### Requirement: REQ-CLI-003 init

`specworks init` SHALL create the config and `<dir>/changes/archive/`, and
install the agent skills unless `--no-skills` is given. Inside a specworks
project, it SHALL link the new project as a module (named by its full path)
using the workspace's config name, unless `--no-link` is given, and SHALL refuse
another `--dir`, or a folder that holds a module of the workspace (naming it),
before writing anything. It SHALL refuse a folder that is not inside a git
repository, saying to run `git init`, before writing anything.
`--diagram-theme` SHALL apply only to a
new top-level config; elsewhere it SHALL print a note saying it wasn't applied.

#### Scenario: AC-CLI-003.1 A new project

- **GIVEN** the folder is empty and inside a git repository
- **WHEN** `init` runs there
- **THEN** it creates the config, `<dir>/changes/archive/` and the skills

#### Scenario: AC-CLI-003.2 Inside a project

- **WHEN** `init <path>` runs inside a project (or a module)
- **THEN** the folder is linked as a module, named `parent/child` when nested, with no skills folder of its own

#### Scenario: AC-CLI-003.3 An independent project

- **WHEN** `init --no-link` runs inside a project
- **THEN** the folder isn't linked, may use another `--dir`, and is a top level of its own

#### Scenario: AC-CLI-003.4 Another --dir for a module

- **WHEN** `init <path> --dir docs` runs inside a workspace that uses `spec`
- **THEN** it fails and writes nothing (no folder, no link)

#### Scenario: AC-CLI-003.5 A theme that cannot apply

- **WHEN** `--diagram-theme` is given for an existing project
- **THEN** init succeeds and says `--diagram-theme not applied`

#### Scenario: AC-CLI-003.6 A folder around an existing module

- **GIVEN** module `billing` at `services/billing`
- **WHEN** `init services` runs from the top level
- **THEN** it is refused naming module `billing`, nothing is written (no config, no link), and the workspace still loads

#### Scenario: AC-CLI-003.7 Outside a git repository

- **GIVEN** a folder that is in no git repository
- **WHEN** `init` runs there
- **THEN** it fails saying to run `git init`, and writes nothing (no config, no folder, no skills)

### Requirement: REQ-CLI-006 Creating, moving and dropping changes

`new` SHALL create a change in the module nearest the working directory, or in
`--module`, and put it on its own branch: it creates and switches to the
change's branch unless `--no-branch` is given, and it SHALL fail without
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
