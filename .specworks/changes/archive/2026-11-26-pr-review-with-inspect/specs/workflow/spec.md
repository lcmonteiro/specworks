## ADDED Requirements

### Requirement: REQ-FLOW-020 Inspection notes by turn

The system SHALL read a change's open inspection findings, active or
archived, and split them by whose turn they are: a finding routed to inspect
(REQ-FLOW-010) is the reviewer's, to confirm; any other open finding is the
author's, to work. Each SHALL be given with its ID and the step it is routed
to, in the order of inspection.md. Done findings and unreadable checkboxes
SHALL be left out, and a change with no inspection.md SHALL have no notes.

#### Scenario: AC-FLOW-020.1 Both turns

- **GIVEN** inspection.md with an open `code-gap` I1, an open `question` I2, an open `code-gap` I3 with `done in code:` and `done in review:`, and a done I4
- **WHEN** its notes are read by turn
- **THEN** the author's are I1 (code) and I2 (review), the reviewer's is I3 (inspect), and I4 is in neither

#### Scenario: AC-FLOW-020.2 A note sent back to specify

- **GIVEN** an open I1 whose Proposal says `back to specify: add the limit`
- **WHEN** its notes are read by turn
- **THEN** I1 is the author's, with step specify

#### Scenario: AC-FLOW-020.3 An archived change

- **GIVEN** a closed change whose archived inspection.md has an open I1
- **WHEN** its notes are read by turn
- **THEN** I1 is the author's, read from the archive folder

#### Scenario: AC-FLOW-020.4 No notes

- **GIVEN** a change with no inspection.md, and another whose inspection.md has only done findings and an unreadable checkbox
- **WHEN** their notes are read by turn
- **THEN** both have none for either turn, and nothing fails

## MODIFIED Requirements

### Requirement: REQ-FLOW-001 Artifact states

The system SHALL report each artifact of a change (refinement, proposal, specs,
design, tasks, traceability, review, validation, inspection) as `done` when its file exists, as
`skipped` for the delta specs of a change marked skip-specs, and otherwise as
`ready` when every artifact it requires is done, optional or skipped, or as
`blocked`. Inspection SHALL be reported as `open` instead of `done` while its
file has at least one open finding (REQ-FLOW-020), for an active or an
archived change. For a change in implement, the status SHALL also report each half
(test, code) with its tasks done and its tasks in total, read from tasks.md
without running any command.

#### Scenario: AC-FLOW-001.1 After planning

- **GIVEN** a change with proposal, delta specs and tasks written
- **WHEN** its status is read
- **THEN** those are `done`, and refinement, design, traceability and review are `ready`

#### Scenario: AC-FLOW-001.2 A written refinement

- **WHEN** a change's refinement.md is written
- **THEN** its status shows refinement as `done`

#### Scenario: AC-FLOW-001.3 A change without behaviour change

- **GIVEN** a change marked skip-specs, with a proposal
- **WHEN** its status is read
- **THEN** specs is `skipped` and tasks is `ready`

#### Scenario: AC-FLOW-001.4 The halves of implement

- **GIVEN** a change in implement whose tasks.md has three `[test]` tasks, all done, and four `[code]` tasks, one done
- **WHEN** its status is read
- **THEN** it shows the test half at 3 of 3 tasks and the code half at 1 of 4; a change in another phase shows no halves

#### Scenario: AC-FLOW-001.5 Validation

- **GIVEN** a change with review.md written
- **WHEN** its status is read before and after validation.md is written
- **THEN** validation is `ready` and optional before, and `done` after

#### Scenario: AC-FLOW-001.6 Inspection

- **GIVEN** a change with tasks.md written
- **WHEN** its status is read before inspection.md is written, after it is written with no finding, and after an open I1 is added to it
- **THEN** inspection is `ready` and optional, then `done`, then `open`

#### Scenario: AC-FLOW-001.7 Inspection confirmed

- **GIVEN** a closed change whose archived inspection.md has an open I1 and a done I2
- **WHEN** its status is read before and after I1 is confirmed (`- [x] I1`)
- **THEN** inspection is `open` before and `done` after
