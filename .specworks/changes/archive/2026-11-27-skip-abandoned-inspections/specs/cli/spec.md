## MODIFIED Requirements

### Requirement: REQ-CLI-025 status shows inspection notes

`status` of a closed change with open inspection notes (REQ-FLOW-020)
SHALL show them by turn, each turn with its IDs and the skill to run:
`/specworks-reopen <ref>` for the author's, `/specworks-inspect <ref>` for the
reviewer's. `--json` SHALL carry them in the change as `inspection`, with
`author` and `reviewer` lists of `{id, step}`, each list present only when it
has a note. An active change, an abandoned change, and a closed change with
no open note, SHALL have no `inspection`.

#### Scenario: AC-CLI-025.1 Notes for the author

- **GIVEN** a closed change `xpto` whose archived inspection.md has open I1 (code-gap) and I2 (question)
- **WHEN** `status --change xpto` runs, with and without `--json`
- **THEN** the text names I1 and I2 for the author with `/specworks-reopen xpto`, and the JSON has `inspection.author` `[{id: I1, step: code}, {id: I2, step: review}]` and no `inspection.reviewer`

#### Scenario: AC-CLI-025.2 A note for the reviewer

- **GIVEN** a closed change `xpto` whose archived I1 has `done in review:` and is still open
- **WHEN** `status --change xpto --json` runs
- **THEN** `inspection.reviewer` is `[{id: I1, step: inspect}]`, there is no `inspection.author`, and the text names I1 for the reviewer with `/specworks-inspect xpto`

#### Scenario: AC-CLI-025.3 Nothing open, or an active change

- **GIVEN** a closed change whose inspection.md has only done findings, a closed change with no inspection.md, and an active change with an open I1
- **WHEN** `status --change <ref> --json` runs for each
- **THEN** none has `inspection`, and the text of none names an inspection turn

#### Scenario: AC-CLI-025.4 An abandoned change

- **GIVEN** an abandoned change `dropped` whose archived inspection.md has an open I1 (code-gap)
- **WHEN** `status --change dropped` runs, with and without `--json`
- **THEN** the JSON has no `inspection`, and the text names no inspection turn and no `/specworks-reopen`

### Requirement: REQ-CLI-026 list --archived shows inspection notes

`list --archived` SHALL give each closed change with open inspection notes
the same `inspection` as `status` (REQ-CLI-025) in `--json`, and in its text
line the number of notes for each turn that has any; other rows, abandoned
changes' included, SHALL be unchanged.

#### Scenario: AC-CLI-026.1 A row with notes

- **GIVEN** two closed changes, `xpto` with open I1 and I2 for the author and one note for the reviewer, and `other` with no inspection.md
- **WHEN** `list --archived` runs, with and without `--json`
- **THEN** `xpto`'s row has `inspection` with two author notes and one reviewer note, and its line says 2 for the author and 1 for the reviewer; `other`'s row has no `inspection` and its line is as before

#### Scenario: AC-CLI-026.2 An abandoned row

- **GIVEN** an abandoned change `dropped` whose archived inspection.md has an open I1
- **WHEN** `list --archived` runs, with and without `--json`
- **THEN** `dropped`'s row has no `inspection`, and its line has no `inspection:` suffix

### Requirement: REQ-CLI-027 context lists inspected changes

`context` SHALL show `inspected`: the closed changes of the current module
(every module with `--all`) that have open inspection notes, each as its
change row with `inspection` (REQ-CLI-025); an empty list when there is none.
An abandoned change SHALL never be listed. `changes` SHALL keep listing
active changes only. The text output SHALL list each inspected change with
the skill its notes wait for.

#### Scenario: AC-CLI-027.1 An inspected change

- **GIVEN** no active change and a closed change `xpto` with an open I1 for the author
- **WHEN** `context --json` runs
- **THEN** `changes` is empty and `inspected` holds `xpto` with its `path` in the archive and `inspection.author` `[{id: I1, step: code}]`; the text output lists `xpto` with `/specworks-reopen xpto`

#### Scenario: AC-CLI-027.2 Nothing inspected

- **GIVEN** closed changes with no open inspection note
- **WHEN** `context --json` runs
- **THEN** `inspected` is an empty list

#### Scenario: AC-CLI-027.3 Other modules

- **GIVEN** a module `billing` with a closed change `inv` that has an open I1, and the current module is the top level
- **WHEN** `context --json` runs without and with `--all`
- **THEN** `inspected` is empty without `--all`, and holds `billing:inv` with `--all`

#### Scenario: AC-CLI-027.4 An abandoned change

- **GIVEN** an abandoned change `dropped` with an open I1 for the author, and a closed change `xpto` with an open I1
- **WHEN** `context --json` runs
- **THEN** `inspected` holds `xpto` only, and the text output does not name `dropped`
