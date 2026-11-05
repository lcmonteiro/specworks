## ADDED Requirements

### Requirement: REQ-CLI-020 reopen

`specworks reopen --change <ref> --reason "<why>" [--phase <phase>]` SHALL move
a closed change back to the active changes (REQ-PROJ-033), in the phase given
(`review` by default), recording the reason (REQ-PROJ-034), and print where the
change is and its phase; under `--json` it SHALL print the change with its
`reopened` entries. It SHALL need `--reason`. It SHALL refuse, with an error
naming why and exit 1, a change that is active, unknown or abandoned, and a
phase it cannot take. It SHALL change no branch, make no commit, and touch no
living spec: the change is committed afterwards like any phase.

#### Scenario: AC-CLI-020.1 Reopening

- **GIVEN** a closed change `add-x`
- **WHEN** `reopen --change add-x --reason "CI lint failed"` runs
- **THEN** the change is in `.specworks/changes/active/add-x` in phase `review`, the output names that path and phase, and `--json` holds the `reopened` entry with the reason

#### Scenario: AC-CLI-020.2 A phase

- **GIVEN** a closed change `add-x`
- **WHEN** `reopen --change add-x --reason "scope changed" --phase refine` runs
- **THEN** the change is in phase `refine`

#### Scenario: AC-CLI-020.3 The reason is needed

- **GIVEN** a closed change `add-x`
- **WHEN** `reopen --change add-x` runs without `--reason`, and again with `--reason "  "`
- **THEN** each fails, and the change is still archived

#### Scenario: AC-CLI-020.4 Refused

- **GIVEN** an active change, an abandoned change and a closed change
- **WHEN** `reopen` names the active one, the abandoned one, a name no change has, and the closed one with `--phase done`
- **THEN** each exits 1 with an error naming the reason (under `--json` as `{"error": ...}`), and no change moves

#### Scenario: AC-CLI-020.5 Git and the living docs untouched

- **GIVEN** a repository with a closed change on its own branch
- **WHEN** `reopen` runs
- **THEN** the checked-out branch and the commit are the same, and no living spec or requirements.md changed

#### Scenario: AC-CLI-020.6 Committed afterwards

- **GIVEN** a reopened change
- **WHEN** `commit --change <ref>` runs
- **THEN** the commit holds the files of the active folder and the removal of the archive folder, and reports nothing of them as already dirty

### Requirement: REQ-CLI-021 status shows a reopen

`status` SHALL show a change that has been reopened with its latest reason, and
`--json` SHALL carry every `reopened` entry (when, reason, phase) in the
change; a change never reopened SHALL have no `reopened` in its `--json`.

#### Scenario: AC-CLI-021.1 A reopened change

- **GIVEN** a change reopened with the reason `CI lint failed`
- **WHEN** `status --change <ref>` runs
- **THEN** its text says it was reopened and why, and `--json` holds the entry

#### Scenario: AC-CLI-021.2 Never reopened

- **GIVEN** a change never reopened
- **WHEN** `status --change <ref> --json` runs
- **THEN** the change has no `reopened`

## MODIFIED Requirements

### Requirement: REQ-CLI-002 Naming a change

A change SHALL be named as `module:name` (exact) or by its bare name: the
current module's first, else the only module that has one. A bare name in
several other modules SHALL be refused, listing the qualified names. An archived
change SHALL be refused by every command but `status` and `reopen`, which read
it by name or by archive folder. A path into the archive is not a change name.

#### Scenario: AC-CLI-002.1 A bare name in another module

- **WHEN** a bare name exists only in another module
- **THEN** it resolves to that module's change (`billing/tax:add-vat`)

#### Scenario: AC-CLI-002.2 The same name in several modules

- **WHEN** a bare name exists in several modules but not the current one
- **THEN** the command fails listing `billing:cleanup` and `billing/tax:cleanup`; a qualified name works

#### Scenario: AC-CLI-002.3 The current module first

- **WHEN** a bare name exists in the current module and another one
- **THEN** the current module's change is used

#### Scenario: AC-CLI-002.4 An archived change

- **WHEN** a command other than `status` or `reopen` names an archived change, or a name no module has
- **THEN** it fails saying where the change is archived, or that it is not found, active or archived

#### Scenario: AC-CLI-002.5 Status of an archived change

- **WHEN** `status` names an archived change by name or by archive folder
- **THEN** it shows the change as archived, with its path (and its reason if abandoned)

#### Scenario: AC-CLI-002.6 An archive path

- **WHEN** a command names `archive/<date>-<name>`
- **THEN** it is refused as not kebab-case, and the archived change is untouched

#### Scenario: AC-CLI-002.7 Reopen names an archived change

- **WHEN** `reopen` names a closed change by its name or by its archive folder `<date>-<name>`
- **THEN** that change is the one reopened
