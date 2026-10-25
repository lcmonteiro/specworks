# Refinement: fix-validate-test-task-skill

## Problem

`specworks validate` sends every open task to `/specworks-code`, even a
`[test]` task that only the test half can do, or design's stub task. REQ-FLOW-013
says each failure names the phase skill that fixes it, so the report points
the user (and `/specworks-done`) to the wrong phase. Found during the
`parallel-test-code` builds; split out of `skill-tooling-gaps` because it
changes behaviour.

## Context

**Observed:**
- `src/specworks/workflow/validate.py`: the `VALIDATE` table gives each
  check one fixed skill; `(COMPLETENESS, CODE, c.tasks_done)` covers every
  task. `validate_change` sets `fix` from the table; `summary` builds
  `goBackTo` from the failing checks' `fix`.
- `src/specworks/workflow/checks.py`: `tasks_done` lists every open task;
  `half_tasks_done(half)` lists the open tasks of one half (`[test]` or
  `[code]`), used by `gate test` and `gate code`. No gate checks tasks with
  no marker.
- `src/specworks/specs/tasks.py`: `Task.half` is `"test"`, `"code"` or `""`
  (no marker).
- The tasks instruction leaves only the design-phase task (the API stubs)
  without a marker.
- `tests/test_validate_phase.py` AC-FLOW-013.3 opens task 1.2 and expects
  `every task is done (specworks task list --pending)` with
  `/specworks-code`.
- Living docs: `src/specworks/workflow/docs/` (REQ-FLOW-013).

**Assumed:**
- Older changes with no markers at all are archived; one still active would
  now be sent to `/specworks-design` for its open tasks.

## Constraints

- [hard] Every check keeps exactly one skill in `fix` (the report and
  `goBackTo` shapes stay the same).
- [hard] `gate validate` applies the same checks (REQ-FLOW-013).
- [soft] Reuse `half_tasks_done` rather than a new way to filter tasks.

## Options

### Option A: Split the check by kind of task

Replace `tasks_done` in `VALIDATE` with three checks: `[test]` tasks →
`/specworks-test`, `[code]` tasks → `/specworks-code`, tasks with no marker
→ `/specworks-design`. Each lists only its own open tasks.

- **Pros:** one skill per check, as today; reuses the gates' check; the
  report says exactly which half is behind.
- **Cons:** the completeness group grows from one task row to three; the
  check name `every task is done` changes, so AC-FLOW-013.3 changes.
- **Effort:** S
- **Touches:** `workflow`

### Option B: One check whose skill depends on the open tasks

Keep one row and pick its skill from the open tasks.

- **Pros:** the report keeps one row.
- **Cons:** a mix of open tasks needs several skills for one check, which
  changes the `fix` field and `goBackTo`.
- **Effort:** S-M
- **Touches:** `workflow`

### Option C: Separate files for test and code tasks

Discussed and set aside: it would also end the `tasks.md` merge conflict
between the halves, but it splits each requirement's plan across files,
leaves design's stub task without a home, and changes the parser, check,
trace, status, gates and skills. Not a fix; a refinement of its own if the
conflict keeps hurting.

## Recommendation

Option A, agreed with the user, with tasks that have no marker sent to
`/specworks-design` (the user's choice over `/specworks-code`).

## Open Questions

None.

## Candidate Capabilities

- `workflow`: modified - REQ-FLOW-013 (validate names the phase per kind of
  open task).
