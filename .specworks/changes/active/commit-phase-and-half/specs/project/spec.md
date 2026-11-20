# Spec Delta: project

## ADDED Requirements

### Requirement: REQ-PROJ-036 A phase commit's subject

The subject of a phase commit SHALL start with the prefix `<ref>: <phase>`, where the phase is `close`
for a change that close has archived; in implement the prefix SHALL be `<ref>: implement (<half>)` with
the given half, `test` or `code`. A given message SHALL follow the prefix as `<prefix> - <message>`,
except a message that already starts with the prefix, which SHALL be the subject as it is; a blank
message SHALL leave the prefix alone. It SHALL refuse, before staging anything, a commit in implement
without a half, a half given in any other phase, a half other than `test` or `code`, and a message of
more than one line.

#### Scenario: AC-PROJ-036.1 The phase

- **GIVEN** a change `add-login` in review
- **WHEN** its phase is committed with no message
- **THEN** the subject is `add-login: review`

#### Scenario: AC-PROJ-036.2 The half

- **GIVEN** a change `add-login` in implement
- **WHEN** its phase is committed with the half `test`, then again with `code`
- **THEN** the subjects are `add-login: implement (test)` and `add-login: implement (code)`

#### Scenario: AC-PROJ-036.3 A message follows the prefix

- **GIVEN** a change `add-login` in implement
- **WHEN** its phase is committed with the half `test` and the message `cycle 2`
- **THEN** the subject is `add-login: implement (test) - cycle 2`

#### Scenario: AC-PROJ-036.4 A message that already has the prefix

- **GIVEN** a change `add-login` in review
- **WHEN** its phase is committed with the message `add-login: review (R1 decided)`
- **THEN** the subject is `add-login: review (R1 decided)`, the prefix not doubled

#### Scenario: AC-PROJ-036.5 A blank message

- **GIVEN** a change `add-login` in design
- **WHEN** its phase is committed with the message `  `
- **THEN** the subject is `add-login: design`

#### Scenario: AC-PROJ-036.6 No half in implement

- **GIVEN** a change `add-login` in implement with changed files
- **WHEN** its phase is committed with no half
- **THEN** it is refused, saying to give `--half test` or `--half code`, and nothing is staged or committed

#### Scenario: AC-PROJ-036.7 A half outside implement

- **GIVEN** a change `add-login` in review, and one that close has archived
- **WHEN** either is committed with the half `test`
- **THEN** it is refused, saying a half is only for implement, and nothing is committed

#### Scenario: AC-PROJ-036.8 An unknown half

- **GIVEN** a change `add-login` in implement
- **WHEN** its phase is committed with the half `docs`
- **THEN** it is refused, naming `test` and `code`, and nothing is committed

#### Scenario: AC-PROJ-036.9 A message on two lines

- **GIVEN** a change `add-login` in design
- **WHEN** its phase is committed with the message `one` and `two` on two lines
- **THEN** it is refused, saying the message is one line (trailers go in `--trailer`), and nothing is committed

#### Scenario: AC-PROJ-036.10 After close

- **GIVEN** a change `add-login` that close has just archived
- **WHEN** it is committed with the message `inspect`
- **THEN** the subject is `add-login: close - inspect`

## MODIFIED Requirements

### Requirement: REQ-PROJ-024 Committing a phase

The system SHALL commit a change's phase by staging only the change's folder
and every dirty or untracked file that its record does not name or whose
content differs from the record, and committing them with the subject of
REQ-PROJ-036, then a blank line and the given trailers in order. It SHALL
report the dirty files it left out and the committed files outside the
change's folder that were already dirty when the phase started.
A change that close has archived SHALL be committed the same way, from its
archive folder, with the default subject `<ref>: close`. With nothing to stage, it
SHALL create no commit and say so. It SHALL never push, and SHALL refuse a
detached HEAD before staging anything.

#### Scenario: AC-PROJ-024.1 Only the phase's files

- **GIVEN** a change recorded when `notes.txt` was dirty, and since then `src/a.py` edited, `tests/test_a.py` created and the change's `tasks.md` edited
- **WHEN** the phase is committed
- **THEN** the commit holds `src/a.py`, `tests/test_a.py` and `tasks.md`, not `notes.txt`, which is reported as left out and still dirty

#### Scenario: AC-PROJ-024.2 Already dirty and changed again

- **GIVEN** a change recorded when `notes.txt` was dirty, and `notes.txt` edited again since
- **WHEN** the phase is committed
- **THEN** `notes.txt` is committed and reported as already dirty when the phase started

#### Scenario: AC-PROJ-024.3 The message

- **GIVEN** a change `add-login` in design
- **WHEN** its phase is committed with the trailers `Co-Authored-By: A <a@x>` and `Session: s1`
- **THEN** the commit message is `add-login: design`, a blank line, then the two trailers in that order; with a given message `stubs`, the subject is `add-login: design - stubs`

#### Scenario: AC-PROJ-024.4 Nothing to commit

- **GIVEN** a change whose folder is clean and no file changed since its record
- **WHEN** the phase is committed
- **THEN** no commit is created and it says there is nothing to commit

#### Scenario: AC-PROJ-024.5 Detached HEAD

- **WHEN** the phase is committed on a detached HEAD
- **THEN** it is refused, saying to switch to a branch, and nothing is staged

#### Scenario: AC-PROJ-024.6 After close

- **GIVEN** a change `add-login` that close has just archived
- **WHEN** its phase is committed
- **THEN** the commit holds its archive folder and the removal of its active folder, with the subject `add-login: close`

#### Scenario: AC-PROJ-024.7 The change's own files are not flagged

- **GIVEN** a change recorded when its `.change.yaml` was dirty, and `.change.yaml` changed again since
- **WHEN** the phase is committed
- **THEN** `.change.yaml` is committed and not reported as already dirty
