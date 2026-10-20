# Spec Delta: project

## ADDED Requirements

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
