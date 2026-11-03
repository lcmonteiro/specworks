## ADDED Requirements

### Requirement: REQ-PROJ-029 A project's docs folder

The system SHALL give the top level and every module a docs folder,
`<its root>/<docs_dir>` (`docs` by default), holding its architecture as
`architecture.md` and that file's diagrams in `diagrams/`. A capability whose
path is the module's folder (`.`) SHALL share that docs folder and still load,
since the file names do not overlap.

#### Scenario: AC-PROJ-029.1 The top level's docs folder

- **GIVEN** a project with the default `docs_dir`
- **WHEN** the workspace is loaded
- **THEN** the top level's docs folder is `docs` and its architecture is `docs/architecture.md`, whether or not they exist

#### Scenario: AC-PROJ-029.2 A module's docs folder

- **GIVEN** module `billing` at `services/billing` whose config sets `docs_dir: doc`
- **WHEN** the workspace is loaded
- **THEN** billing's docs folder is `services/billing/doc`, and its architecture `services/billing/doc/architecture.md`

#### Scenario: AC-PROJ-029.3 A capability on the module's folder

- **GIVEN** a capability `core` with path `.`
- **WHEN** the workspace is loaded
- **THEN** it loads, and `core`'s docs folder and the top level's are both `docs`
