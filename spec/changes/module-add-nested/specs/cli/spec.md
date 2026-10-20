# Spec Delta: cli

## MODIFIED Requirements

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
