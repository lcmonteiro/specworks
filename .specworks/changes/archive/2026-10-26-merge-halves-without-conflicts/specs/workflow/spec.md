## ADDED Requirements

### Requirement: REQ-FLOW-015 Merging a half's branch

The system SHALL merge a branch into the current checkout with git, for a
change. When the merge conflicts only in that change's `tasks.md` and
`traceability.md`, it SHALL resolve them and commit the merge: in `tasks.md`
a task SHALL be done when either side ticked it, and `traceability.md` SHALL be
regenerated. A `tasks.md` line that differs between the sides in more than its
box, or a conflict in any other file, SHALL abort the merge and leave the
checkout as it was before, naming the conflicting files. It SHALL refuse,
before merging, a checkout with uncommitted changes or a branch that does not
exist.

#### Scenario: AC-FLOW-015.1 No conflict

- **GIVEN** a branch that changed only test files
- **WHEN** it is merged for the change
- **THEN** the merge is committed and nothing is reported as resolved

#### Scenario: AC-FLOW-015.2 Ticks on both sides

- **GIVEN** a branch that ticked a `[test]` task and a checkout that ticked a nearby `[code]` task in the same `tasks.md`
- **WHEN** the branch is merged for the change
- **THEN** the merge is committed, both tasks are ticked, and `tasks.md` is reported as resolved

#### Scenario: AC-FLOW-015.3 The trace on both sides

- **GIVEN** a branch and a checkout that both rewrote the change's `traceability.md`
- **WHEN** the branch is merged for the change
- **THEN** the merge is committed with `traceability.md` regenerated from the merged code and tests, and reported as resolved

#### Scenario: AC-FLOW-015.4 Another file conflicts

- **GIVEN** a branch and a checkout that changed the same lines of a source file
- **WHEN** the branch is merged for the change
- **THEN** it fails naming that file, the merge is aborted, and the checkout's files and HEAD are as before

#### Scenario: AC-FLOW-015.5 A task's text differs

- **GIVEN** a branch and a checkout whose `tasks.md` differ on a line in more than its box
- **WHEN** the branch is merged for the change
- **THEN** it fails naming `tasks.md`, and the merge is aborted with the checkout as before

#### Scenario: AC-FLOW-015.6 Uncommitted changes or an unknown branch

- **WHEN** the checkout has uncommitted changes, or the branch does not exist
- **THEN** it fails before merging, saying which, and nothing changes
