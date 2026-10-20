# Spec Delta: cli

## MODIFIED Requirements

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
