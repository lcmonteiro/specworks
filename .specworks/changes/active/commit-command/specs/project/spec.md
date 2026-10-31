# Spec Delta: project

## ADDED Requirements

### Requirement: REQ-PROJ-023 The files dirty when a phase starts

When a change is created or its phase changes, the system SHALL record in
the change's metadata every file of the workspace that git reports as
staged, unstaged or untracked (not ignored), by its path relative to the
workspace root, with a SHA-256 of its content or `deleted` when it no longer
exists. Moving a change to the phase it is already in SHALL keep the record
it has. A change whose metadata has no record (created before this) SHALL be
read as having none.

#### Scenario: AC-PROJ-023.1 Recorded at a phase move

- **GIVEN** a workspace where `notes.txt` is modified, `draft.md` is untracked and `old.txt` is deleted
- **WHEN** a change is moved from specify to design
- **THEN** its metadata records the three paths: the first two with the SHA-256 of their content, `old.txt` as `deleted`

#### Scenario: AC-PROJ-023.2 Same phase, same record

- **GIVEN** a change in implement, recorded when `notes.txt` was the only dirty file, and `src/a.py` edited since
- **WHEN** it is moved to implement again
- **THEN** its record still names only `notes.txt`

#### Scenario: AC-PROJ-023.3 No record yet

- **GIVEN** a change whose metadata has no record
- **WHEN** it is read
- **THEN** it loads, with no recorded files

### Requirement: REQ-PROJ-024 Committing a phase

The system SHALL commit a change's phase by staging only the change's folder
and every dirty or untracked file that its record does not name or whose
content differs from the record, and committing them with the subject
`<ref>: <phase>` or a given one, then a blank line and the given trailers in
order. It SHALL report the dirty files it left out and the committed files
that were already dirty when the phase started. With nothing to stage, it
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
