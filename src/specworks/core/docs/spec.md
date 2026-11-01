# project

## Purpose

The project model: where a specworks project is and how its config is read and
written, the workspace of modules linked to it, the changes in flight and their
phases, and running the project's own commands.

## Requirements

### Requirement: REQ-PROJ-001 Finding the project config

The system SHALL treat as the project config a `.specworks/config.yml` file
holding a `specworks: <n>` line, with `.specworks/` as the workflow folder, and
find the project by walking up from the working directory to the nearest folder
that holds one.

#### Scenario: AC-PROJ-001.1 The fixed workflow folder

- **GIVEN** a project whose config is `.specworks/config.yml`
- **WHEN** a change is created
- **THEN** it goes to `.specworks/changes/active/<name>`

#### Scenario: AC-PROJ-001.2 A config.yml without the marker is not a config

- **GIVEN** a folder whose `.specworks/config.yml` has no `specworks:` line, or is not UTF-8 text
- **WHEN** the project is looked up
- **THEN** that file is ignored and no project is found there

#### Scenario: AC-PROJ-001.4 No project

- **GIVEN** no specworks config in the working directory or any of its parents
- **WHEN** the project is looked up
- **THEN** no project is found (the CLI reports `"root": null` and exits 1)

#### Scenario: AC-PROJ-001.5 Found from a subfolder

- **GIVEN** a working directory below a project's folder, but holding no config itself
- **WHEN** the project is looked up
- **THEN** the nearest config above it is used

#### Scenario: AC-PROJ-001.6 Other YAML files are not configs

- **GIVEN** a folder holding a `*.yml` without the marker and no `.specworks/config.yml`
- **WHEN** the project is looked up
- **THEN** no project is found there

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
- **THEN** loading fails saying `'dir' is no longer a setting` and that the workflow folder is always `.specworks/`

### Requirement: REQ-PROJ-003 Config value checks

The system SHALL reject a config whose values have the wrong shape, with an
error naming the setting: paths that leave the project, globs that are not a
list of `*`/`?`/`**` patterns, a context that is not text or is larger than
51200 bytes, commands that are not a mapping of test, lint, typecheck, build or
format to a command string, diagram settings that are not a known theme, a
known layout (elk or dagre), a true/false sketch and a non-negative pad, and
`tools` that is not a non-empty list of known tool IDs or is set in a module's
config.

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

#### Scenario: AC-PROJ-003.6 Tools

- **WHEN** `tools` is not a list, is empty, or holds an unknown tool (e.g. `cursor`)
- **THEN** loading fails naming `tools` and the known tool IDs

#### Scenario: AC-PROJ-003.7 Tools in a module

- **WHEN** a module's config sets `tools`
- **THEN** loading fails saying `tools` is set in the top level's config

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
its config lists (recursively), each a project with its own
`.specworks/config.yml`. A module's folder (with symlinks resolved) SHALL be
inside the top level's, or loading SHALL fail naming the module and where its
folder is. A folder SHALL be at most one module: a module whose folder (with
symlinks resolved) is an ancestor or another module of the workspace SHALL make
loading fail, naming both. A module SHALL be listed by the innermost
module whose folder contains it: one listed by a module further up SHALL make
loading fail, naming the module it belongs under. Looking up the workspace, it SHALL rise from the
nearest config to each ancestor that lists it as a module.

#### Scenario: AC-PROJ-006.1 The whole workspace from inside a module

- **GIVEN** a working directory inside a nested module
- **WHEN** the workspace is loaded
- **THEN** its root is the top-level project and the current module is the nested one (`billing/tax`)

#### Scenario: AC-PROJ-006.2 A listed module without a config

- **WHEN** a module listed by its parent has no config in its folder
- **THEN** the workspace still loads and reports it as missing, with its name and path

#### Scenario: AC-PROJ-006.4 A broken unrelated outer config

- **GIVEN** a project inside a folder whose broken config does not list it as a module
- **WHEN** the inner project's workspace is loaded
- **THEN** it loads, ignoring the outer config

#### Scenario: AC-PROJ-006.5 A broken parent that lists the module

- **GIVEN** a broken config that lists the current project as a module
- **WHEN** the workspace is loaded
- **THEN** loading fails with that config's error

#### Scenario: AC-PROJ-006.6 A module that leads back to an ancestor

- **GIVEN** a project listing `loop: loop`, where `loop` is a symlink to the project's own folder
- **WHEN** the workspace is loaded
- **THEN** it fails (no crash) naming module `loop` and `(top)`, the module whose folder it already is

#### Scenario: AC-PROJ-006.7 A folder linked as a module twice

- **GIVEN** a folder linked as module `billing` and, through a symlink, as module `other`
- **WHEN** the workspace is loaded
- **THEN** it fails naming both `billing` and `other` and the folder

#### Scenario: AC-PROJ-006.8 A module listed past the module that contains it

- **GIVEN** a top level listing `billing: services/billing` and `sub: services/billing/sub`
- **WHEN** the workspace is loaded
- **THEN** it fails naming module `sub` and `billing`, the module it belongs under

#### Scenario: AC-PROJ-006.9 A module outside the workspace

- **GIVEN** a project listing `ext: ext`, where `ext` is a symlink to a folder outside the project
- **WHEN** the workspace is loaded
- **THEN** it fails (no crash) naming module `ext` and the folder it leads to, whether or not that folder has a config

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

The system SHALL write a new project's config as `.specworks/config.yml`
starting with `specworks: 1`, and set the diagram theme when one is given.

#### Scenario: AC-PROJ-009.1 Written in the fixed folder

- **WHEN** a project is initialised
- **THEN** `.specworks/config.yml` is its config and starts with `specworks: 1`

#### Scenario: AC-PROJ-009.3 Diagram theme

- **WHEN** a theme is given by name (e.g. `Cool Classics`)
- **THEN** the config sets it under its canonical name (`cool-classics`); an unknown theme is refused and no config is written

### Requirement: REQ-PROJ-010 Creating a change

The system SHALL create a change as a folder under `.specworks/changes/active/`
named after it, starting in the `refine` phase and recording when it started.
The name must be kebab-case, must not be `archive` or `active`, must not be in
use, and must not be the name of an archived change.

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

- **WHEN** the name is `archive` or `active`, or names an archived change
- **THEN** it is refused, saying the name is reserved or where the change was archived

### Requirement: REQ-PROJ-011 Change phases

The system SHALL track a change through the phases refine, specify, design,
implement, review, validate, close and done, letting a change move to any of
them except `done`, which only closing reaches. `test` and `code` SHALL NOT be
phases: a change whose metadata names `test` or `code` (saved before
`implement` existed) SHALL be read as being in `implement`, and moving a change
to `test` or `code` SHALL be refused, naming `implement`. A change whose
metadata cannot be read SHALL be an error naming its file.

#### Scenario: AC-PROJ-011.1 Moving between phases

- **WHEN** a change is moved to a phase, forward or back
- **THEN** its phase is that one, and the phases are listed in workflow order

#### Scenario: AC-PROJ-011.2 Done only through close

- **WHEN** a change is moved to `done` directly
- **THEN** it is refused, saying only close makes a change done

#### Scenario: AC-PROJ-011.3 Broken metadata

- **WHEN** a change's `.change.yaml` is not a mapping, is not YAML, or names an unknown phase
- **THEN** reading the change fails with an error naming the file and the problem

#### Scenario: AC-PROJ-011.4 A change saved in test or code

- **GIVEN** a change whose `.change.yaml` says `phase: test` (or `phase: code`)
- **WHEN** the change is read
- **THEN** its phase is `implement`

#### Scenario: AC-PROJ-011.5 Test and code are not phases

- **WHEN** a change is moved to `test` or `code`
- **THEN** it is refused, naming `implement`, and its phase is unchanged

### Requirement: REQ-PROJ-012 Archived changes

The system SHALL list archived changes from the `<date>-<name>` folders of the
archive, oldest first, leaving out folders that are misnamed or whose metadata
cannot be read.

#### Scenario: AC-PROJ-012.1 Listing the archive

- **GIVEN** an archived change, a misnamed folder and a folder with broken metadata in the archive
- **WHEN** archived changes are listed
- **THEN** only the archived change is listed, by its name

#### Scenario: AC-PROJ-012.2 Oldest first

- **GIVEN** changes archived on two different days
- **WHEN** archived changes are listed
- **THEN** the one archived on the earlier day comes first

### Requirement: REQ-PROJ-013 Running the project's commands

The system SHALL run a configured command (`commands.<key>`, merged from the
top level down to the module) through the shell in the module's folder, and
report its exit code and output. A key that is not a command key (`test`,
`lint`, `typecheck`, `build`, `format`) SHALL be an error listing the valid
keys. A command key that is not configured SHALL be an error saying where to
add it, with an example for that key.

#### Scenario: AC-PROJ-013.1 Exit code and output

- **WHEN** a configured command runs
- **THEN** its exit code and the tail of its output are reported

#### Scenario: AC-PROJ-013.2 In the module's folder

- **WHEN** a module's command runs
- **THEN** it runs in that module's folder

#### Scenario: AC-PROJ-013.3 Not configured

- **WHEN** a command that is not configured is run
- **THEN** it fails with `no '<key>' command configured`, the config to add it to, and an example for that key (`lint: <command>`)

#### Scenario: AC-PROJ-013.4 Not a command key

- **WHEN** a key that is not a command key, such as `frobnicate`, is run
- **THEN** it fails with `unknown command 'frobnicate'` listing `test, lint, typecheck, build, format`, and doesn't suggest adding it to the config

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

### Requirement: REQ-PROJ-015 Reading project files

The system SHALL report a project file that is not UTF-8 text as an error
naming the file and asking to save it as UTF-8, instead of crashing.

#### Scenario: AC-PROJ-015.1 A file that is not UTF-8

- **WHEN** a project file the workflow reads (e.g. a delta spec) is not UTF-8
- **THEN** the command fails with `is not UTF-8 text` and the file's name

### Requirement: REQ-PROJ-016 Unique docs folders

The system SHALL refuse to load a workspace in which two capabilities, in any
modules, resolve to the same living-docs folder (`<module root>/<path>/<docs_dir>`),
with an error naming both capabilities and the folder. Capabilities whose paths
are nested SHALL still load. Registering a capability that would share a docs
folder SHALL be refused, leaving the config unchanged.

#### Scenario: AC-PROJ-016.1 Two capabilities on one path

- **GIVEN** a config with capabilities `auth` and `login`, both on `src/auth` (written the same or with a trailing `/`)
- **WHEN** the workspace is loaded
- **THEN** it fails naming `auth`, `login` and `src/auth/docs`

#### Scenario: AC-PROJ-016.2 Across modules

- **GIVEN** a top-level capability on `services/billing/src/invoices` and a capability of module `billing` (at `services/billing`) on `src/invoices`
- **WHEN** the workspace is loaded
- **THEN** it fails naming both capabilities (`billing:invoices` for the module's)

#### Scenario: AC-PROJ-016.3 Nested paths

- **GIVEN** capabilities on `src/auth` and `src/auth/admin`
- **WHEN** the workspace is loaded
- **THEN** it loads, and each capability has its own docs folder

#### Scenario: AC-PROJ-016.4 Registering one on a taken path

- **WHEN** `capability add login --path src/auth` runs while `auth` is on `src/auth`
- **THEN** it fails naming `auth`, and the config file is unchanged

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

### Requirement: REQ-PROJ-020 Where changes live

The system SHALL keep changes in flight in `.specworks/changes/active/` and
archived ones in `.specworks/changes/archive/`. A folder with change metadata
that sits directly under `.specworks/changes/` SHALL NOT be a change: it is not
listed and cannot be named.

#### Scenario: AC-PROJ-020.1 Active changes are listed from active

- **GIVEN** a change created in the project
- **WHEN** the active changes are listed
- **THEN** the change is found, and its folder is `.specworks/changes/active/<name>`

#### Scenario: AC-PROJ-020.2 A loose folder is not a change

- **GIVEN** a folder `.specworks/changes/<name>` holding a `.change.yaml`, outside `active/` and `archive/`
- **WHEN** the active changes are listed, or the change is named
- **THEN** it is not listed, and naming it fails saying the change is not found

#### Scenario: AC-PROJ-020.3 Archived changes stay in archive

- **GIVEN** a change in `.specworks/changes/active/`
- **WHEN** it is closed or abandoned
- **THEN** it is in `.specworks/changes/archive/<date>-<name>` and no longer under `active/`

### Requirement: REQ-PROJ-021 The old config layout

When no project is found, but the working directory or one of its parents holds
an old-style config (a `*.yml` holding a `specworks: <n>` line), the system
SHALL fail with an error naming that file and the move to make
(`<dir>.yml` to `.specworks/config.yml`, `<dir>/` to `.specworks/`). A module
listed by its parent whose folder has an old-style config and no
`.specworks/config.yml` SHALL fail the same way, and so SHALL `init` in a folder
that holds an old-style config and no `.specworks/config.yml`. The system SHALL
move nothing.

#### Scenario: AC-PROJ-021.1 An old project

- **GIVEN** a folder holding `spec.yml` with `specworks: 1` and a `spec/` folder, and no `.specworks/config.yml`
- **WHEN** a command looks up the project there or below it
- **THEN** it fails naming `spec.yml` and saying to move it to `.specworks/config.yml` and `spec/` to `.specworks/`; no file is moved

#### Scenario: AC-PROJ-021.2 An old module

- **GIVEN** a workspace listing module `billing`, whose folder holds `spec.yml` with `specworks: 1` and no `.specworks/config.yml`
- **WHEN** the workspace is loaded
- **THEN** it fails naming module `billing`, its `spec.yml` and the move to make

#### Scenario: AC-PROJ-021.3 A new project wins

- **GIVEN** a folder holding both `.specworks/config.yml` and an old `spec.yml`
- **WHEN** the project is looked up
- **THEN** `.specworks/config.yml` is used and the old file is ignored

#### Scenario: AC-PROJ-021.4 An old project is not re-initialised

- **GIVEN** a folder holding `spec.yml` with `specworks: 1` and no `.specworks/config.yml`
- **WHEN** `init` runs there, with or without `--no-link`
- **THEN** it fails with the old-layout error naming `spec.yml` and the move, and writes nothing (no `.specworks/`, no skills, no link)

### Requirement: REQ-PROJ-022 Saving the tools

The system SHALL save the AI tools a project uses as a `tools:` list of tool
IDs in the top level's config, editing it as text: the user's comments and
other entries SHALL be kept, and a `tools:` list already there SHALL be
replaced. When the edit would not give the expected config, it SHALL leave the
file unchanged and say to set `tools` by hand.

#### Scenario: AC-PROJ-022.1 Saved with the comments kept

- **GIVEN** a config with comments and no `tools`
- **WHEN** the tools `claude` and `copilot` are saved
- **THEN** the config has `tools: [claude, copilot]`, its comments are still there, and it loads with those tools

#### Scenario: AC-PROJ-022.2 Replaced

- **GIVEN** a config that saves `tools: [claude]`
- **WHEN** the tool `copilot` is saved
- **THEN** the config has one `tools:` entry, `tools: [copilot]`

#### Scenario: AC-PROJ-022.3 A list the text edit cannot replace

- **GIVEN** a config with two `tools:` entries
- **WHEN** the tool `copilot` is saved
- **THEN** the config file is unchanged and the error says to set `tools` by hand

### Requirement: REQ-PROJ-023 The files dirty when a phase starts

When a change is created or its phase changes, the system SHALL record in
the change's metadata every file of the workspace that git reports as
staged, unstaged or untracked (not ignored), by its path relative to the
workspace root, with a SHA-256 of its content or `deleted` when it no longer
exists. Moving a change to the phase it is already in SHALL keep the record
it has. A change whose metadata has no record (created before this) SHALL be
read as having none. Outside a git repository, the move SHALL still
succeed, with no record.

#### Scenario: AC-PROJ-023.1 Recorded at a phase move

- **GIVEN** a workspace where `notes.txt` is modified, `draft.md` is untracked and `old.txt` is deleted
- **WHEN** a change is moved from specify to design
- **THEN** its metadata records the three paths: the first two with the SHA-256 of their content, `old.txt` as `deleted`

#### Scenario: AC-PROJ-023.2 Same phase, same record

- **GIVEN** a change in implement, recorded when `notes.txt` was the only dirty file, and `src/a.py` edited since
- **WHEN** it is moved to implement again
- **THEN** its record still names only `notes.txt`

#### Scenario: AC-PROJ-023.3 No record yet

- **GIVEN** a change whose metadata has no record
- **WHEN** it is read
- **THEN** it loads, with no recorded files

#### Scenario: AC-PROJ-023.4 Outside a git repository

- **GIVEN** a change whose workspace is in no git repository
- **WHEN** it is moved from specify to design
- **THEN** its phase is design and it has no recorded files

### Requirement: REQ-PROJ-024 Committing a phase

The system SHALL commit a change's phase by staging only the change's folder
and every dirty or untracked file that its record does not name or whose
content differs from the record, and committing them with the subject
`<ref>: <phase>` or a given one, then a blank line and the given trailers in
order. It SHALL report the dirty files it left out and the committed files
that were already dirty when the phase started. With nothing to stage, it
SHALL create no commit and say so. It SHALL never push, and SHALL refuse a
detached HEAD before staging anything.

#### Scenario: AC-PROJ-024.1 Only the phase's files

- **GIVEN** a change recorded when `notes.txt` was dirty, and since then `src/a.py` edited, `tests/test_a.py` created and the change's `tasks.md` edited
- **WHEN** the phase is committed
- **THEN** the commit holds `src/a.py`, `tests/test_a.py` and `tasks.md`, not `notes.txt`, which is reported as left out and still dirty

#### Scenario: AC-PROJ-024.2 Already dirty and changed again

- **GIVEN** a change recorded when `notes.txt` was dirty, and `notes.txt` edited again since
- **WHEN** the phase is committed
- **THEN** `notes.txt` is committed and reported as already dirty when the phase started

#### Scenario: AC-PROJ-024.3 The message

- **GIVEN** a change `add-login` in design
- **WHEN** its phase is committed with the trailers `Co-Authored-By: A <a@x>` and `Session: s1`
- **THEN** the commit message is `add-login: design`, a blank line, then the two trailers in that order; with a given subject, that subject replaces `add-login: design`

#### Scenario: AC-PROJ-024.4 Nothing to commit

- **GIVEN** a change whose folder is clean and no file changed since its record
- **WHEN** the phase is committed
- **THEN** no commit is created and it says there is nothing to commit

#### Scenario: AC-PROJ-024.5 Detached HEAD

- **WHEN** the phase is committed on a detached HEAD
- **THEN** it is refused, saying to switch to a branch, and nothing is staged
