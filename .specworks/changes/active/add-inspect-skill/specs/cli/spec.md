# Spec Delta: cli

## MODIFIED Requirements

### Requirement: REQ-CLI-002 Naming a change

A change SHALL be named as `module:name` (exact) or by its bare name: the
current module's first, else the only module that has one. A bare name in
several other modules SHALL be refused, listing the qualified names. An archived
change SHALL be refused by every command but `status`, `reopen`, `trace`
without `--write`, and `finding` on its inspection.md (`finding add
--artifact inspection`, or an `I<n>` ID), which read it by name or by archive
folder; `finding` on any other check artifact of an archived change, and
`trace --write`, SHALL be refused saying where the change is archived. A path into the archive is not a change name.

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

- **WHEN** a command other than `status`, `reopen`, `trace` or `finding` names an archived change, or a name no module has
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

#### Scenario: AC-CLI-002.8 Trace of an archived change

- **WHEN** `trace --change <name> --json` names a closed change, then `trace --write` does
- **THEN** the first exits 0 with the change's matrix; the second is refused saying where the change is archived, and no file changes

#### Scenario: AC-CLI-002.9 Inspection notes on an archived change

- **WHEN** `finding add question "x" --proposal "back to review: y" --artifact inspection --change <name> --json` names a closed change, then the same with `--artifact review`
- **THEN** the first exits 0 and writes I1 to inspection.md in the change's archive folder; the second is refused saying where the change is archived, and no file changes
