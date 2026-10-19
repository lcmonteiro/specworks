# Spec Delta: project

## Purpose

The project model: where a specworks project is and how its config is read and
written, the workspace of modules linked to it, the changes in flight and their
phases, and running the project's own commands.

## ADDED Requirements

### Requirement: REQ-PROJ-001 Finding the project config

The system SHALL treat as the project config a `<dir>.yml` file holding a
`specworks: <n>` line, name the workflow folder after the file (`spec.yml` ->
`spec/`), and find the project by walking up from the working directory to the
nearest folder that holds a config.

#### Scenario: AC-PROJ-001.1 The file name sets the workflow folder

- **GIVEN** a project whose config is `<dir>.yml`, or was renamed to another name
- **WHEN** a change is created
- **THEN** it goes to `<dir>/changes/<name>`, `<dir>` being the config file's name without `.yml`

#### Scenario: AC-PROJ-001.2 A YAML file without the marker is not a config

- **GIVEN** a folder whose only `.yml` file has no `specworks:` line, or is not UTF-8 text
- **WHEN** the project is looked up
- **THEN** that file is ignored and no project is found there

#### Scenario: AC-PROJ-001.3 Several configs in one folder

- **GIVEN** a folder holding two specworks configs
- **WHEN** the project is loaded
- **THEN** it fails with an error saying the folder has several specworks configs

#### Scenario: AC-PROJ-001.4 No project

- **GIVEN** no specworks config in the working directory or any of its parents
- **WHEN** the project is looked up
- **THEN** no project is found (the CLI reports `"root": null` and exits 1)

#### Scenario: AC-PROJ-001.5 Found from a subfolder

- **GIVEN** a working directory below a project's folder, but holding no config itself
- **WHEN** the project is looked up
- **THEN** the nearest config above it is used

### Requirement: REQ-PROJ-002 Config file checks

The system SHALL reject a config that is not readable YAML, does not declare
the supported version (`specworks: 1`), holds unknown keys or still sets the
old `dir` key, with an error naming the problem.

#### Scenario: AC-PROJ-002.1 Unsupported version

- **WHEN** the config says `specworks: 2`
- **THEN** loading fails with `unsupported config version specworks: 2 (expected 1)`

#### Scenario: AC-PROJ-002.2 Unreadable YAML

- **WHEN** the config is not valid YAML
- **THEN** loading fails with `cannot read <config>`

#### Scenario: AC-PROJ-002.3 Unknown keys

- **WHEN** the config, or one of its capabilities, has a key specworks does not know (e.g. `capabilites`, `prefx`)
- **THEN** loading fails naming the unknown keys

#### Scenario: AC-PROJ-002.4 The old dir key

- **WHEN** the config sets `dir:`
- **THEN** loading fails saying `'dir' is no longer a setting` and that the file name sets the folder

### Requirement: REQ-PROJ-003 Config value checks

The system SHALL reject a config whose values have the wrong shape, with an
error naming the setting: paths that leave the project, globs that are not a
list of `*`/`?`/`**` patterns, a context that is not text or is larger than
51200 bytes, commands that are not a mapping of test, lint, typecheck, build or
format to a command string, and diagram settings that are not a known theme, a
known layout (elk or dagre), a true/false sketch and a non-negative pad.

#### Scenario: AC-PROJ-003.1 Paths stay inside the project

- **WHEN** `docs_dir`, a capability path or a module path is absolute, contains `..` or is not a non-empty string
- **THEN** loading (or adding the entry) fails saying it must be a relative folder inside the project

#### Scenario: AC-PROJ-003.2 Globs

- **WHEN** `test_globs` or `source_globs` is a single string, holds a non-string, or uses `[..]` or `{..}`
- **THEN** loading fails with a message naming the key (for a single string, showing it as a list)

#### Scenario: AC-PROJ-003.3 Context

- **WHEN** `context` is not a string, or is larger than 51200 bytes
- **THEN** loading fails saying so

#### Scenario: AC-PROJ-003.4 Commands

- **WHEN** `commands` is not a mapping, or a command is not a string
- **THEN** loading fails naming `commands` (with the allowed keys) or `commands.<key>`

#### Scenario: AC-PROJ-003.5 Diagram settings

- **WHEN** `diagrams.theme` or `diagrams.dark_theme` is not a known theme, or `diagrams.pad` is not a non-negative number
- **THEN** loading fails naming the setting; `dark_theme: none` is accepted and means the light theme is used in dark mode too

### Requirement: REQ-PROJ-004 Capabilities in the config

The system SHALL read each capability as a kebab-case name with a code path,
given either as `name: path` or as a mapping with `path`, an optional
`prefix` and an optional `description`, and SHALL derive its requirement ID
prefix, when none is given, from its module path and name in upper case.

#### Scenario: AC-PROJ-004.1 Name and path only

- **WHEN** a capability is given as `user-auth: src/auth/`
- **THEN** its path is `src/auth` and its prefix is `USER-AUTH`

#### Scenario: AC-PROJ-004.2 Prefix inside a module

- **GIVEN** a capability `invoices` in module `billing`, with no `prefix`
- **WHEN** the workspace is loaded
- **THEN** its prefix is `BILLING-INVOICES`

#### Scenario: AC-PROJ-004.3 Empty description

- **WHEN** a capability's `description:` is empty
- **THEN** its description is the empty string

#### Scenario: AC-PROJ-004.4 Name must be kebab-case

- **WHEN** a capability name is not kebab-case (e.g. `Bad_Name`)
- **THEN** it is rejected with a message saying it must be kebab-case

### Requirement: REQ-PROJ-005 Unique ID prefixes

The system SHALL refuse to load a workspace in which two capabilities, in any
modules, have the same requirement ID prefix, given or derived.

#### Scenario: AC-PROJ-005.1 Two capabilities share a prefix

- **WHEN** two capabilities use the same prefix (both given, or one given and one derived, or both derived across modules)
- **THEN** loading fails naming both capabilities and the prefix, and suggests giving one its own `prefix:`

### Requirement: REQ-PROJ-006 Workspace of modules

The system SHALL load a workspace made of a top-level project and the modules
its config lists (recursively), each a project with its own config of the same
file name. Looking up the workspace, it SHALL rise from the nearest config to
each ancestor that lists it as a module.

#### Scenario: AC-PROJ-006.1 The whole workspace from inside a module

- **GIVEN** a working directory inside a nested module
- **WHEN** the workspace is loaded
- **THEN** its root is the top-level project and the current module is the nested one (`billing/tax`)

#### Scenario: AC-PROJ-006.2 A listed module without a config

- **WHEN** a module listed by its parent has no config in its folder
- **THEN** the workspace still loads and reports it as missing, with its name and path

#### Scenario: AC-PROJ-006.3 A module with another config name

- **WHEN** a module's config file name differs from the top level's
- **THEN** loading fails naming both file names and asking to rename the module's file and folder

#### Scenario: AC-PROJ-006.4 A broken unrelated outer config

- **GIVEN** a project inside a folder whose broken config does not list it as a module
- **WHEN** the inner project's workspace is loaded
- **THEN** it loads, ignoring the outer config

#### Scenario: AC-PROJ-006.5 A broken parent that lists the module

- **GIVEN** a broken config that lists the current project as a module
- **WHEN** the workspace is loaded
- **THEN** loading fails with that config's error

### Requirement: REQ-PROJ-007 What a module inherits

The system SHALL give a module the context of every project from the top level
down to it, in that order, and the commands of the top level overridden key by
key by each module down to it.

#### Scenario: AC-PROJ-007.1 Inherited context

- **GIVEN** a top level and a module that both have context
- **WHEN** the context of a module below them is read
- **THEN** it holds the top level's context first, then the module's

#### Scenario: AC-PROJ-007.2 Inherited and overridden commands

- **GIVEN** a top level that sets `test` and `lint`, and a module that sets only `test`
- **WHEN** the module's commands are read
- **THEN** `test` is the module's and `lint` is the top level's

### Requirement: REQ-PROJ-008 Adding entries to the config

The system SHALL add a module or a capability to a config by editing it as
text, keeping the user's comments and existing entries. It SHALL refuse a
name already in use, a module path already linked, and SHALL leave the file
unchanged, asking to add the entry by hand, when the edit would not give the
expected config.

#### Scenario: AC-PROJ-008.1 Comments are kept

- **WHEN** a module is added
- **THEN** the config's comments are still there and the entry is under `modules:`

#### Scenario: AC-PROJ-008.2 A capability entry

- **WHEN** a capability is added with a path and a description
- **THEN** the config gets `<name>:`, `path:` and the quoted `description:` under `capabilities:`

#### Scenario: AC-PROJ-008.3 Duplicates

- **WHEN** a module or capability name already exists, or a module path is already linked
- **THEN** the entry is refused saying it already exists or is already linked

#### Scenario: AC-PROJ-008.4 An entry the text edit cannot add

- **GIVEN** a `capabilities:` block written as a flow mapping
- **WHEN** a capability is added
- **THEN** the config file is left unchanged and the error asks to add it by hand

### Requirement: REQ-PROJ-009 Default config

The system SHALL write a new project's config as `<dir>.yml` starting with
`specworks: 1`, refusing a folder name that is not a single name of letters,
digits, `-` or `_`, and setting the diagram theme when one is given.

#### Scenario: AC-PROJ-009.1 Written under the folder's name

- **WHEN** a project is initialised with folder `<dir>`
- **THEN** `<dir>.yml` is the only config and starts with `specworks: 1`

#### Scenario: AC-PROJ-009.2 Bad folder names

- **WHEN** the folder is absolute, `..`, `.`, empty, nested or hidden
- **THEN** it is refused and no config is written

#### Scenario: AC-PROJ-009.3 Diagram theme

- **WHEN** a theme is given by name (e.g. `Cool Classics`)
- **THEN** the config sets it under its canonical name (`cool-classics`); an unknown theme is refused and no config is written

### Requirement: REQ-PROJ-010 Creating a change

The system SHALL create a change as a folder under `<dir>/changes/` named after
it, starting in the `refine` phase and recording when it started. The name must
be kebab-case, must not be `archive`, must not be in use, and must not be the
name of an archived change.

#### Scenario: AC-PROJ-010.1 A new change

- **WHEN** a change is created
- **THEN** it is in phase `refine` and its metadata records `created` as a date and time

#### Scenario: AC-PROJ-010.2 Names that are not kebab-case

- **WHEN** the name is not kebab-case (`Add_Login`, `add login`, `x--y`, `archive-`)
- **THEN** it is refused with a message saying it must be kebab-case

#### Scenario: AC-PROJ-010.3 A name in use

- **WHEN** a change of that name already exists
- **THEN** it is refused saying it already exists

#### Scenario: AC-PROJ-010.4 Reserved and archived names

- **WHEN** the name is `archive`, or names an archived change
- **THEN** it is refused, saying `archive` is reserved or where the change was archived

### Requirement: REQ-PROJ-011 Change phases

The system SHALL track a change through the phases refine, specify, design,
test, code, review, validate, close and done, letting a change move to any of
them except `done`, which only closing reaches. A change whose metadata cannot
be read SHALL be an error naming its file.

#### Scenario: AC-PROJ-011.1 Moving between phases

- **WHEN** a change is moved to a phase, forward or back
- **THEN** its phase is that one, and the phases are listed in workflow order

#### Scenario: AC-PROJ-011.2 Done only through close

- **WHEN** a change is moved to `done` directly
- **THEN** it is refused, saying only close makes a change done

#### Scenario: AC-PROJ-011.3 Broken metadata

- **WHEN** a change's `.change.yaml` is not a mapping, is not YAML, or names an unknown phase
- **THEN** reading the change fails with an error naming the file and the problem

### Requirement: REQ-PROJ-012 Archived changes

The system SHALL list archived changes from the `<date>-<name>` folders of the
archive, oldest first, leaving out folders that are misnamed or whose metadata
cannot be read.

#### Scenario: AC-PROJ-012.1 Listing the archive

- **GIVEN** an archived change, a misnamed folder and a folder with broken metadata in the archive
- **WHEN** archived changes are listed
- **THEN** only the archived change is listed, by its name

### Requirement: REQ-PROJ-013 Running the project's commands

The system SHALL run a configured command (`commands.<key>`, merged from the
top level down to the module) through the shell in the module's folder, and
report its exit code and output. A command that is not configured SHALL be an
error saying where to add it.

#### Scenario: AC-PROJ-013.1 Exit code and output

- **WHEN** a configured command runs
- **THEN** its exit code and the tail of its output are reported

#### Scenario: AC-PROJ-013.2 In the module's folder

- **WHEN** a module's command runs
- **THEN** it runs in that module's folder

#### Scenario: AC-PROJ-013.3 Not configured

- **WHEN** a command that is not configured is run
- **THEN** it fails with `no '<key>' command configured` and the config to add it to

### Requirement: REQ-PROJ-014 Reusing command results

The system SHALL reuse the result of a command run on an identical working tree
(same command and folder, same `HEAD`, same uncommitted changes, same untracked
files and contents, the workflow folders left out), passing or failing. Every
real run SHALL replace the recorded result for its tree. Reuse SHALL be off
without git, when `SPECWORKS_RUN_CACHE=0`, and when a git submodule holds
untracked files.

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

### Requirement: REQ-PROJ-015 Reading project files

The system SHALL report a project file that is not UTF-8 text as an error
naming the file and asking to save it as UTF-8, instead of crashing.

#### Scenario: AC-PROJ-015.1 A file that is not UTF-8

- **WHEN** a project file the workflow reads (e.g. a delta spec) is not UTF-8
- **THEN** the command fails with `is not UTF-8 text` and the file's name
