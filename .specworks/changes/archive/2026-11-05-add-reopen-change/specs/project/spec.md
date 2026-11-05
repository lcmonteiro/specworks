## ADDED Requirements

### Requirement: REQ-PROJ-033 Reopening a closed change

The system SHALL reopen a closed change by moving its folder from
`.specworks/changes/archive/<date>-<name>/` back to
`.specworks/changes/active/<name>/` with every file in it, and by setting the
phase it is given: any phase but `done`, which only closing reaches
(REQ-PROJ-011). It SHALL keep the change's name, creation time and files, and
SHALL record the dirty files before it moves anything, as a phase move does
(REQ-PROJ-023). It SHALL refuse a change that is not archived, one that was
abandoned, one whose name is already in use in `active/`, and a phase it cannot
move to, changing nothing. When the move fails, the change SHALL stay archived
with its metadata as it was.

#### Scenario: AC-PROJ-033.1 Back to active

- **GIVEN** a closed change `add-x` in `.specworks/changes/archive/<date>-add-x` with a proposal and an `events.jsonl`
- **WHEN** it is reopened to `review`
- **THEN** `.specworks/changes/active/add-x` holds the same files, the archive folder is gone, the phase is `review` and `created` is unchanged

#### Scenario: AC-PROJ-033.2 Any phase but done

- **GIVEN** a closed change
- **WHEN** it is reopened to `refine`, and another one to `implement`
- **THEN** each is in the phase it was given

#### Scenario: AC-PROJ-033.3 A phase it cannot take

- **GIVEN** a closed change
- **WHEN** it is reopened to `done`, to `test` or to a phase that does not exist
- **THEN** it is refused as a phase move is, and the change is still archived and unchanged

#### Scenario: AC-PROJ-033.4 Not a closed change

- **GIVEN** an active change, an abandoned archived change and a name no change has
- **WHEN** each is reopened
- **THEN** each is refused, saying it is not archived, that it was abandoned, or that it is not found, and nothing moves

#### Scenario: AC-PROJ-033.5 A name already in use

- **GIVEN** a closed change `add-x` and an active folder `add-x`
- **WHEN** `add-x` is reopened
- **THEN** it is refused saying the active change exists, and neither folder changes

#### Scenario: AC-PROJ-033.6 Dirty files recorded before the move

- **GIVEN** a workspace where `notes.txt` is modified and a closed change is archived
- **WHEN** the change is reopened
- **THEN** its metadata records `notes.txt` and not the files the move removed from the archive

#### Scenario: AC-PROJ-033.7 A move that fails

- **GIVEN** a closed change and a move that fails
- **WHEN** it is reopened
- **THEN** the error is raised, the change is still in the archive, and its metadata is as it was

#### Scenario: AC-PROJ-033.8 The same identity

- **GIVEN** a closed change with recorded events
- **WHEN** it is reopened
- **THEN** its `events.jsonl` is in the active folder with the same lines, and its trace ID is the one it had before

### Requirement: REQ-PROJ-034 The reopen record

Reopening a change SHALL need a reason with text, and SHALL add to the change's
metadata a `reopened` entry holding when it was reopened (date and time), the
reason and the phase it started in. The entries SHALL be kept, oldest first, when
the change is archived and reopened again, and a change whose metadata has none
SHALL be read as never reopened.

#### Scenario: AC-PROJ-034.1 The entry

- **GIVEN** a closed change
- **WHEN** it is reopened to `review` with the reason `CI lint failed`
- **THEN** its metadata has one `reopened` entry with the date and time, `CI lint failed` and `review`

#### Scenario: AC-PROJ-034.2 Reopened twice

- **GIVEN** a change reopened once, then closed again
- **WHEN** it is reopened with another reason
- **THEN** its metadata has two entries, the first reason before the second

#### Scenario: AC-PROJ-034.3 A blank reason

- **GIVEN** a closed change
- **WHEN** it is reopened with an empty reason, or one of spaces
- **THEN** it is refused saying why a reason is needed, and the change is still archived

#### Scenario: AC-PROJ-034.4 Never reopened

- **GIVEN** a change whose metadata has no `reopened`
- **WHEN** it is read
- **THEN** it loads, with no reopen entries
