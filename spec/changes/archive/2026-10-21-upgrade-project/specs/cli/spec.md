## ADDED Requirements

### Requirement: REQ-CLI-009 update

`update` SHALL bring the workspace's skills up to the running CLI. It refreshes
the tools that have `specworks-…` skills installed (`--tools` overrides them;
with none installed it uses `auto`, as `skills` does). It SHALL write only the
files that differ or are missing, printing `updated <path>` for each, and
remove the stale ones, printing `removed <path>`. When nothing needs a change,
it SHALL write nothing and print `skills up to date`. Run from a module, it
SHALL update the workspace root's skills.

#### Scenario: AC-CLI-009.1 Outdated skills

- **GIVEN** installed skills where one skill file was edited, another deleted, and a `specworks-propose` folder added
- **WHEN** `update` runs
- **THEN** it prints `updated` for the two files and `removed` for `specworks-propose`, and the skills state is then `current`

#### Scenario: AC-CLI-009.2 Already up to date

- **GIVEN** skills just installed
- **WHEN** `update` runs
- **THEN** it prints `skills up to date` and no installed file is rewritten

#### Scenario: AC-CLI-009.3 Keeps the installed tools

- **GIVEN** a project with only Claude Code skills installed and a `.github/copilot-instructions.md`
- **WHEN** `update` runs
- **THEN** it refreshes the Claude Code skills and writes no Copilot skill or prompt file

#### Scenario: AC-CLI-009.4 From a module

- **WHEN** `update` runs inside a module's folder
- **THEN** the workspace root's skills are updated and the module gets no skills folder

## MODIFIED Requirements

### Requirement: REQ-CLI-004 Overview commands

`context` SHALL show the workspace: root, current module, inherited context,
commands, modules (and missing ones), every capability with its docs path,
prefix and delta path, the changes, and the skills state (`skills`: `current`,
`outdated` with its files, or `none`). When the skills are outdated, it SHALL
also show the hint `skills out of date: run specworks update`. `list` SHALL
list the current module's active changes (every module's with `--all`,
archived ones with `--archived`), flagging an active change that also has an
archived copy. `module list` SHALL show every module with the current one
marked.

#### Scenario: AC-CLI-004.1 Context

- **WHEN** `context` runs
- **THEN** each capability shows its docs path and whether it has a living spec

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
