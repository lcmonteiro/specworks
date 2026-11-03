## MODIFIED Requirements

### Requirement: REQ-CLI-004 Overview commands

`context` SHALL show the workspace: root, current module, inherited context,
commands, modules (and missing ones), every capability with its docs path,
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
