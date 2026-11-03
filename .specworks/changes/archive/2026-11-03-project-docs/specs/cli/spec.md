## MODIFIED Requirements

### Requirement: REQ-CLI-004 Overview commands

`context` SHALL show the workspace: root, current module, inherited context,
commands, modules (and missing ones) each with its docs folder (`docsPath`)
and whether it holds `architecture.md` (`hasArchitecture`), every capability with its docs path,
test folder (`testsPath`), prefix and delta path, the changes, and the skills state (`skills`: `current`,
`outdated` with its files, or `none`). When the skills are outdated, it SHALL
also show the hint `skills out of date: run specworks update`. `list` SHALL
list the current module's active changes (every module's with `--all`,
archived ones with `--archived`), flagging an active change that also has an
archived copy. `module list` SHALL show every module with the current one
marked.

#### Scenario: AC-CLI-004.1 Context

- **WHEN** `context` runs
- **THEN** each capability shows its docs path, its test folder (`testsPath`, relative to the workspace root, whether or not it exists) and whether it has a living spec

#### Scenario: AC-CLI-004.2 All modules

- **WHEN** `list` runs with and without `--all`
- **THEN** it lists the current module's changes, or every module's

#### Scenario: AC-CLI-004.3 Archived and leftover changes

- **WHEN** `list --archived` runs, or an active change has an archived copy
- **THEN** archived changes are listed with their date and state, and the leftover copy is flagged with `alsoArchived`

#### Scenario: AC-CLI-004.4 Module tree

- **WHEN** `module list` runs
- **THEN** it lists `(top)` and every module, the current one marked

#### Scenario: AC-CLI-004.5 Skills state

- **GIVEN** installed skills where one skill file was edited
- **WHEN** `context` runs, with and without `--json`
- **THEN** the JSON has `skills` with state `outdated` and that file, and the text output shows `skills out of date: run specworks update`; with current skills, the JSON state is `current` and there is no hint

#### Scenario: AC-CLI-004.6 Each module's docs folder

- **GIVEN** a top level with `docs/architecture.md` and module `billing` at `services/billing` without one
- **WHEN** `context --json` runs
- **THEN** the `(top)` entry of `modules` has `docsPath` `docs` and `hasArchitecture` true, and `billing`'s has `docsPath` `services/billing/docs` and `hasArchitecture` false

### Requirement: REQ-CLI-007 close

`close` SHALL run validate first and refuse a change that doesn't pass, naming
the phases to go back to. With `--dry-run` it SHALL show the merge plan and
write nothing. When the change's module has no `architecture.md` in its docs
folder, `close` SHALL refuse before running validate, naming the missing file
and writing nothing, and `--dry-run` SHALL show the plan with that file named
as missing. `--no-run` SHALL be accepted only with `--dry-run`, because the
real close runs the project's commands before writing.

#### Scenario: AC-CLI-007.1 Dry run

- **WHEN** `close --dry-run` runs
- **THEN** it lists each capability's added, modified and removed requirements, and no file changes

#### Scenario: AC-CLI-007.2 no-run

- **WHEN** `close --no-run` runs without `--dry-run`
- **THEN** it fails and writes nothing; with `--dry-run` it is accepted

#### Scenario: AC-CLI-007.3 Validate fails

- **WHEN** the change doesn't pass validate
- **THEN** close fails with `does not pass validate` and `goBackTo`, and the change stays active

#### Scenario: AC-CLI-007.4 No architecture

- **GIVEN** a change whose module has no `docs/architecture.md`
- **WHEN** `close` runs, then `close --dry-run`
- **THEN** close fails naming `docs/architecture.md`, writes nothing and runs no command, and the change stays active; the dry run shows the merge plan and names `docs/architecture.md` as missing
