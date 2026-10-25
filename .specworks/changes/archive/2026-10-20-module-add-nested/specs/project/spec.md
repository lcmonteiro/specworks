# Spec Delta: project

## MODIFIED Requirements

### Requirement: REQ-PROJ-006 Workspace of modules

The system SHALL load a workspace made of a top-level project and the modules
its config lists (recursively), each a project with its own config of the same
file name. A folder SHALL be at most one module: a module whose folder (with
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
