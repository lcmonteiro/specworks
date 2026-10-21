## MODIFIED Requirements

### Requirement: REQ-SPECS-009 Tasks

Tasks SHALL be the `- [ ] N.M text` lines of tasks.md (`- [x]` when done); lines
in code fences and after `## Workflow follow-up` SHALL not be tasks. A task
whose text starts with `[test]` or `[code]` SHALL belong to that half of the
implement phase; a task with neither SHALL belong to no half. `check` SHALL
report a task-like line in another format, a number used twice, a task
naming an ID the change's specs don't have, and an ADDED or MODIFIED criterion
no task names (by its ID or its requirement's); a missing tasks.md SHALL be a
warning and one with no task an error. `check` SHALL warn, without failing,
when the change has ADDED or MODIFIED criteria but no `[test]` task, or ADDED
or MODIFIED requirements but no `[code]` task. Ticking or unticking a task
SHALL change only its checkbox, and SHALL refuse an unknown number.

#### Scenario: AC-SPECS-009.1 Task format and IDs

- **WHEN** tasks.md has a malformed task or a task naming an unknown ID
- **THEN** `check` fails naming the line

#### Scenario: AC-SPECS-009.2 Every criterion has a task

- **WHEN** a criterion of the change is named by no task, nor is its requirement
- **THEN** `check` fails naming the criterion

#### Scenario: AC-SPECS-009.3 Not tasks

- **WHEN** tasks.md shows a task inside a code fence, or lists bullets under `## Workflow follow-up`
- **THEN** they are not tasks

#### Scenario: AC-SPECS-009.4 No tasks yet

- **WHEN** tasks.md is missing, or has no task
- **THEN** `check` warns, or fails asking for `- [ ] 1.1` checkboxes

#### Scenario: AC-SPECS-009.5 Ticking a task

- **WHEN** `task done` and `task undo` run on a task, or on an unknown number
- **THEN** only that task's checkbox changes, or the unknown number is refused listing the tasks

#### Scenario: AC-SPECS-009.6 The half of a task

- **GIVEN** tasks `1.1 Add stubs`, `1.2 [test] Write failing tests` and `1.3 [code] Implement`
- **WHEN** the tasks are read
- **THEN** 1.2 belongs to the test half, 1.3 to the code half, and 1.1 to no half

#### Scenario: AC-SPECS-009.7 A half with no task

- **WHEN** a change has ADDED criteria and requirements but tasks.md has no `[test]` task, or no `[code]` task
- **THEN** `check` passes with a warning naming the missing half
