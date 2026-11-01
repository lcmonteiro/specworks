# Spec Delta: cli

## ADDED Requirements

### Requirement: REQ-CLI-014 Creating a capability's code folder

`capability add` with `--create` SHALL, once the capability is registered,
create its code folder (the path relative to the owning module's root) with
an empty `.gitkeep` when the folder does not exist, and say so in its output:
the `.gitkeep` path relative to the workspace root, or none when nothing was
created. A folder that exists SHALL be left unchanged. A path that exists as
a file SHALL be refused before the config is written. When `capability add`
refuses for any reason, nothing SHALL be created. Without `--create`, no
folder or file SHALL be created.

#### Scenario: AC-CLI-014.1 A missing folder created

- **WHEN** `capability add auth --path src/auth --create --json` runs and `src/auth` does not exist
- **THEN** `src/auth/.gitkeep` exists and is empty, the capability is registered, and the output names `src/auth/.gitkeep` as created

#### Scenario: AC-CLI-014.2 An existing folder left as it is

- **GIVEN** a folder `src/auth` holding a file
- **WHEN** `capability add auth --path src/auth --create --json` runs
- **THEN** the capability is registered, no `.gitkeep` is added, the folder's files are unchanged, and the output names nothing as created

#### Scenario: AC-CLI-014.3 In a module

- **GIVEN** module `billing` at `services/billing`
- **WHEN** `capability add invoices --path src/invoices --module billing --create` runs from the top level
- **THEN** `services/billing/src/invoices/.gitkeep` exists and the capability is registered in billing's config

#### Scenario: AC-CLI-014.4 A refused capability creates nothing

- **GIVEN** a capability already using the ID prefix `AUTH`
- **WHEN** `capability add auth2 --path src/auth2 --prefix AUTH --create` runs
- **THEN** it is refused, `src/auth2` does not exist, and the config is unchanged

#### Scenario: AC-CLI-014.5 A path that is a file

- **GIVEN** a file `src/auth`
- **WHEN** `capability add auth --path src/auth --create --json` runs
- **THEN** it prints `{"error": ...}` naming `src/auth`, exits 1, the file is unchanged, and the config is unchanged

#### Scenario: AC-CLI-014.6 Without --create

- **WHEN** `capability add auth --path src/auth` runs and `src/auth` does not exist
- **THEN** the capability is registered and `src/auth` still does not exist
