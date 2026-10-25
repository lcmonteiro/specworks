# Proposal: fix-validate-test-task-skill

## Why

`specworks validate` sends every open task to `/specworks-code`, even a
`[test]` task or design's stub task, while REQ-FLOW-013 says each failure
names the phase skill that fixes it. The refinement chose Option A: one
check per kind of task.

## What Changes

- Validate's single "every task is done" check is replaced by three
  completeness checks, each listing only its own open tasks:
  - `[test]` tasks → `/specworks-test` (the check `gate test` already uses);
  - `[code]` tasks → `/specworks-code` (the check `gate code` already uses);
  - tasks with no `[test]` or `[code]` marker (design's stub tasks) →
    `/specworks-design`.
- `goBackTo` lists the skills of the failing checks, as today. `gate
  validate` applies the same checks.
- Assumption: an active change written before the markers existed gets its
  open tasks sent to `/specworks-design`; its tasks can be marked to route
  them.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `workflow`: REQ-FLOW-013 (validate: open tasks are reported by kind, each
  naming its phase skill).

## Impact

- `src/specworks/workflow/validate.py` (the `VALIDATE` table),
  `src/specworks/workflow/checks.py` (a check for tasks with no marker),
  `tests/test_validate_phase.py`.
- The validate report: the completeness group has three task checks
  instead of one, and the name `every task is done` is gone.
- No change to `specworks task`, the gates' own checks or the task format.

## Out of Scope

- Splitting `tasks.md` into separate files for test and code tasks.
- Changing which skill any other validate check names.
