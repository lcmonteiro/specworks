# Spec Delta: project

## ADDED Requirements

### Requirement: REQ-PROJ-020 Where changes live

The system SHALL keep changes in flight in `<dir>/changes/active/` and
archived ones in `<dir>/changes/archive/`. A folder with change metadata that
sits directly under `<dir>/changes/` SHALL NOT be a change: it is not listed
and cannot be named.

#### Scenario: AC-PROJ-020.1 Active changes are listed from active

- **GIVEN** a change created in the project
- **WHEN** the active changes are listed
- **THEN** the change is found, and its folder is `<dir>/changes/active/<name>`

#### Scenario: AC-PROJ-020.2 A loose folder is not a change

- **GIVEN** a folder `<dir>/changes/<name>` holding a `.change.yaml`, outside `active/` and `archive/`
- **WHEN** the active changes are listed, or the change is named
- **THEN** it is not listed, and naming it fails saying the change is not found

#### Scenario: AC-PROJ-020.3 Archived changes stay in archive

- **GIVEN** a change in `<dir>/changes/active/`
- **WHEN** it is closed or abandoned
- **THEN** it is in `<dir>/changes/archive/<date>-<name>` and no longer under `active/`

## MODIFIED Requirements

### Requirement: REQ-PROJ-001 Finding the project config

The system SHALL treat as the project config a `<dir>.yml` file holding a
`specworks: <n>` line, name the workflow folder after the file (`spec.yml` ->
`spec/`), and find the project by walking up from the working directory to the
nearest folder that holds a config.

#### Scenario: AC-PROJ-001.1 The file name sets the workflow folder

- **GIVEN** a project whose config is `<dir>.yml`, or was renamed to another name
- **WHEN** a change is created
- **THEN** it goes to `<dir>/changes/active/<name>`, `<dir>` being the config file's name without `.yml`

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

### Requirement: REQ-PROJ-010 Creating a change

The system SHALL create a change as a folder under `<dir>/changes/active/` named
after it, starting in the `refine` phase and recording when it started. The name
must be kebab-case, must not be `archive` or `active`, must not be in use, and
must not be the name of an archived change.

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
