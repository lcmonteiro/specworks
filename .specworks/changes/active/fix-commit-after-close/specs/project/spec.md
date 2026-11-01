# Spec Delta: project

## MODIFIED Requirements

### Requirement: REQ-PROJ-024 Committing a phase

The system SHALL commit a change's phase by staging only the change's folder
and every dirty or untracked file that its record does not name or whose
content differs from the record, and committing them with the subject
`<ref>: <phase>` or a given one, then a blank line and the given trailers in
order. It SHALL report the dirty files it left out and the committed files
outside the change's folder that were already dirty when the phase started.
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
- **THEN** the commit message is `add-login: design`, a blank line, then the two trailers in that order; with a given subject, that subject replaces `add-login: design`

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
