# cli

## Purpose

The `specworks` command line: the conventions every command follows (JSON
output, errors, paths), how a change is named on the command line, and what each
command adds on top of the capabilities it calls.

## Requirements

### Requirement: REQ-CLI-001 Output and errors

Every command an agent reads SHALL support `--json`. An expected failure SHALL
print `{"error": …}` with `--json`, or `error: …` on stderr without it, and exit
1, including a failure raised before a command runs (a broken config or change
file). With no project, the answer SHALL be `{"root": null}` with a fix, and
exit 1. Paths in the output SHALL be relative to the workspace root.

#### Scenario: AC-CLI-001.1 No project

- **WHEN** a command runs where no specworks config is found
- **THEN** it exits 1 and its JSON has `"root": null`

#### Scenario: AC-CLI-001.2 An error

- **WHEN** a change file is broken, whether a command names the change or `list`/`context` read every change
- **THEN** the command exits 1 with `{"error": …}` (`--json`) or `error: …` on stderr

#### Scenario: AC-CLI-001.3 Relative paths

- **WHEN** `init` runs, at the top level or in a module
- **THEN** it prints paths relative to the workspace root, never the absolute root

### Requirement: REQ-CLI-002 Naming a change

A change SHALL be named as `module:name` (exact) or by its bare name: the
current module's first, else the only module that has one. A bare name in
several other modules SHALL be refused, listing the qualified names. An archived
change SHALL be refused by every command but `status`, which reads it by name or
by archive folder. A path into the archive is not a change name.

#### Scenario: AC-CLI-002.1 A bare name in another module

- **WHEN** a bare name exists only in another module
- **THEN** it resolves to that module's change (`billing/tax:add-vat`)

#### Scenario: AC-CLI-002.2 The same name in several modules

- **WHEN** a bare name exists in several modules but not the current one
- **THEN** the command fails listing `billing:cleanup` and `billing/tax:cleanup`; a qualified name works

#### Scenario: AC-CLI-002.3 The current module first

- **WHEN** a bare name exists in the current module and another one
- **THEN** the current module's change is used

#### Scenario: AC-CLI-002.4 An archived change

- **WHEN** a command other than `status` names an archived change, or a name no module has
- **THEN** it fails saying where the change is archived, or that it is not found, active or archived

#### Scenario: AC-CLI-002.5 Status of an archived change

- **WHEN** `status` names an archived change by name or by archive folder
- **THEN** it shows the change as archived, with its path (and its reason if abandoned)

#### Scenario: AC-CLI-002.6 An archive path

- **WHEN** a command names `archive/<date>-<name>`
- **THEN** it is refused as not kebab-case, and the archived change is untouched

### Requirement: REQ-CLI-003 init

`specworks init` SHALL create the config and `<dir>/changes/archive/`, and
install the agent skills unless `--no-skills` is given. Inside a specworks
project, it SHALL link the new project as a module (named by its full path)
using the workspace's config name, unless `--no-link` is given, and SHALL refuse
another `--dir`, or a folder that holds a module of the workspace (naming it),
before writing anything. `--diagram-theme` SHALL apply only to a
new top-level config; elsewhere it SHALL print a note saying it wasn't applied.

#### Scenario: AC-CLI-003.1 A new project

- **WHEN** `init` runs in an empty folder
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

### Requirement: REQ-CLI-004 Overview commands

`context` SHALL show the workspace: root, current module, inherited context,
commands, modules (and missing ones), every capability with its docs path,
prefix and delta path, and the changes. `list` SHALL list the current module's
active changes (every module's with `--all`, archived ones with `--archived`),
flagging an active change that also has an archived copy. `module list` SHALL
show every module with the current one marked.

#### Scenario: AC-CLI-004.1 Context

- **WHEN** `context` runs
- **THEN** each capability shows its docs path and whether it has a living spec

#### Scenario: AC-CLI-004.2 All modules

- **WHEN** `list` runs with and without `--all`
- **THEN** it lists the current module's changes, or every module's

#### Scenario: AC-CLI-004.3 Archived and leftover changes

- **WHEN** `list --archived` runs, or an active change has an archived copy
- **THEN** archived changes are listed with their date and state, and the leftover copy is flagged with `alsoArchived`

#### Scenario: AC-CLI-004.4 Module tree

- **WHEN** `module list` runs
- **THEN** it lists `(top)` and every module, the current one marked

### Requirement: REQ-CLI-005 Registering modules and capabilities

`module add <path>` SHALL refuse a folder that is not inside the current
project, create the module's config with the workspace's name when it has none,
and link it in the config of the innermost module that contains the folder,
printing the folder's full module name. It SHALL refuse a folder that holds a
module of the workspace, naming that module, before writing anything. `capability add` SHALL refuse an ID prefix, given or derived,
already used by another capability, and SHALL register a capability in the
module `--module` names.

#### Scenario: AC-CLI-005.1 Adding a module

- **WHEN** `module add services/billing` runs
- **THEN** the parent lists it and the module has its config and changes folder

#### Scenario: AC-CLI-005.2 A folder with another config

- **WHEN** the folder already has a config under another name
- **THEN** it is refused and nothing is written

#### Scenario: AC-CLI-005.3 A folder outside the project

- **WHEN** the folder is the project itself or outside it
- **THEN** it is refused with `must be a folder inside` the project

#### Scenario: AC-CLI-005.4 A prefix in use

- **WHEN** a capability's prefix (given, or derived from its name) is already used
- **THEN** it is refused naming the capability that uses it, and the config is unchanged

#### Scenario: AC-CLI-005.5 In a module

- **WHEN** `capability add --module billing` runs
- **THEN** the capability is registered in billing's config with its own prefix and paths

#### Scenario: AC-CLI-005.6 A folder inside another module

- **GIVEN** module `billing` at `services/billing`
- **WHEN** `module add services/billing/sub` runs from the top level
- **THEN** billing's config lists `sub: sub`, the top level's config is unchanged, and the output names module `billing/sub`

#### Scenario: AC-CLI-005.7 A folder around an existing module

- **GIVEN** module `billing` at `services/billing`
- **WHEN** `module add services` runs from the top level
- **THEN** it is refused naming module `billing`, no config is written or changed, and the workspace still loads

### Requirement: REQ-CLI-006 Creating, moving and dropping changes

`new` SHALL create a change in the module nearest the working directory, or in
`--module`. `phase <phase> --change <ref>` SHALL move a change without checking
gates, and SHALL refuse the old argument order with a hint. `abandon` SHALL
archive a change without merging, and requires a reason. `skip-specs` SHALL
mark a change as having no behaviour change, and `--off` removes the mark.

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

### Requirement: REQ-CLI-007 close

`close` SHALL run validate first and refuse a change that doesn't pass, naming
the phases to go back to. With `--dry-run` it SHALL show the merge plan and
write nothing. `--no-run` SHALL be accepted only with `--dry-run`, because the
real close runs the project's commands before writing.

#### Scenario: AC-CLI-007.1 Dry run

- **WHEN** `close --dry-run` runs
- **THEN** it lists each capability's added, modified and removed requirements, and no file changes

#### Scenario: AC-CLI-007.2 no-run

- **WHEN** `close --no-run` runs without `--dry-run`
- **THEN** it fails and writes nothing; with `--dry-run` it is accepted

#### Scenario: AC-CLI-007.3 Validate fails

- **WHEN** the change doesn't pass validate
- **THEN** close fails with `does not pass validate` and `goBackTo`, and the change stays active

### Requirement: REQ-CLI-008 diagrams

`diagrams` SHALL render the diagrams of a change (`--change`) or of a folder
inside the workspace (`--dir`), or list the themes (`--themes`) with the ones in
use and the d2 found. It requires one of these. `--check` SHALL only report the
diagrams' states and exit 1 when any is missing or stale. A folder outside the
workspace SHALL be refused.

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
