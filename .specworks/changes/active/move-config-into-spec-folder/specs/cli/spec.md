## MODIFIED Requirements

### Requirement: REQ-CLI-003 init

`specworks init` SHALL create `.specworks/config.yml`,
`.specworks/changes/active/` and `.specworks/changes/archive/`, and
install the agent skills unless `--no-skills` is given. Inside a specworks
project, it SHALL link the new project as a module (named by its full path)
unless `--no-link` is given, and SHALL refuse a folder that holds a module of
the workspace (naming it) before writing anything. It SHALL refuse a folder
that is not inside a git repository, saying to run `git init`, before writing
anything. `--diagram-theme` SHALL apply only to a new top-level config;
elsewhere it SHALL print a note saying it wasn't applied.

#### Scenario: AC-CLI-003.1 A new project

- **GIVEN** the folder is empty and inside a git repository
- **WHEN** `init` runs there
- **THEN** it creates `.specworks/config.yml`, `.specworks/changes/active/`, `.specworks/changes/archive/` and the skills

#### Scenario: AC-CLI-003.2 Inside a project

- **WHEN** `init <path>` runs inside a project (or a module)
- **THEN** the folder is linked as a module, named `parent/child` when nested, with no skills folder of its own

#### Scenario: AC-CLI-003.3 An independent project

- **WHEN** `init --no-link` runs inside a project
- **THEN** the folder isn't linked and is a top level of its own

#### Scenario: AC-CLI-003.5 A theme that cannot apply

- **WHEN** `--diagram-theme` is given for an existing project
- **THEN** init succeeds and says `--diagram-theme not applied`

#### Scenario: AC-CLI-003.6 A folder around an existing module

- **GIVEN** module `billing` at `services/billing`
- **WHEN** `init services` runs from the top level
- **THEN** it is refused naming module `billing`, nothing is written (no config, no link), and the workspace still loads

#### Scenario: AC-CLI-003.7 Outside a git repository

- **GIVEN** a folder that is in no git repository
- **WHEN** `init` runs there
- **THEN** it fails saying to run `git init`, and writes nothing (no config, no folder, no skills)

#### Scenario: AC-CLI-003.8 No --dir option

- **WHEN** `init --dir spec` runs
- **THEN** it fails as an unknown option and writes nothing
