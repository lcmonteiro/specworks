## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: REQ-PROJ-021 The old config layout

When no project is found, but the working directory or one of its parents holds
an old-style config (a `*.yml` holding a `specworks: <n>` line), the system
SHALL fail with an error naming that file and the move to make
(`<dir>.yml` to `.specworks/config.yml`, `<dir>/` to `.specworks/`). A module
listed by its parent whose folder has an old-style config and no
`.specworks/config.yml` SHALL fail the same way. The system SHALL move nothing.

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
