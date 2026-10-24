# Design: fix-validate-test-task-skill

## Context

Validate's `VALIDATE` table (`src/specworks/workflow/validate.py`) gives each
check one fixed skill, and its single `c.tasks_done` row sends every open
task to `/specworks-code`. `gate test` and `gate code` already check one half
each with `half_tasks_done(half)` (`src/specworks/workflow/checks.py`); no
check covers tasks with no `[test]` or `[code]` marker (`Task.half == ""`).
See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- Each kind of open task fails its own validate check, naming its own skill
  (REQ-FLOW-013).

**Non-Goals:**
- Changing the gates' own checks, `specworks task` or the task format.

## Decisions

### A new check for unmarked tasks, next to `half_tasks_done`

Add `unmarked_tasks_done(ctx)` to `checks.py` rather than accepting `""` in
`half_tasks_done(half)`: the half factory builds its name from the marker
(`every [{half}] task is done`), which reads wrong for no marker, and the
gates never check unmarked tasks. It mirrors `half_tasks_done`: it fails
when tasks.md is not found or when an unmarked task is open, listing
`"<num> <text>"` for each. Its name is
`every task with no [test] or [code] marker is done (specworks task list --pending)`.
Alternative name considered: `every unmarked task is done (...)`: shorter,
but "unmarked" is not a word the report uses anywhere else. Serves:
REQ-FLOW-013.

### Validate's table uses the three task checks

In `VALIDATE`, the `(COMPLETENESS, CODE, c.tasks_done)` row becomes three
rows, in this order: `c.half_tasks_done("test")` → `/specworks-test`,
`c.half_tasks_done("code")` → `/specworks-code`, `c.unmarked_tasks_done` →
`/specworks-design` (a new `DESIGN` constant beside `SPECIFY, TEST, CODE,
REVIEW`). `tasks_done` is dropped once nothing uses it (task 1.4). Every
check keeps one skill, so `fix` and `goBackTo` keep their shapes. Serves:
REQ-FLOW-013.

## Interfaces

Agreed with the user

- `src/specworks/workflow/checks.py`: `unmarked_tasks_done(ctx: GateContext) -> Check` (new), a check named
  `every task with no [test] or [code] marker is done (specworks task list --pending)`
  that fails when tasks.md is not found or a task with no `[test]`/`[code]` marker is open, listing
  `"<num> <text>"` for each open one (REQ-FLOW-013)
- `src/specworks/workflow/validate.py`: `VALIDATE` (extended): the `c.tasks_done` row is replaced by
  `c.half_tasks_done("test")` (`/specworks-test`), `c.half_tasks_done("code")` (`/specworks-code`) and
  `c.unmarked_tasks_done` (`/specworks-design`, new constant `DESIGN = "/specworks-design"`); the
  `every task is done` check is gone from the report (REQ-FLOW-013). Not breaking for callers: the
  report's shape is unchanged, only its rows change; the table rows are the code half's work.

## Risks / Trade-offs

- [risk] With tasks.md missing, all three task checks fail and `goBackTo`
  lists test, code and design besides specify -> acceptable: the
  `planning artifacts exist` row already names `/specworks-specify`
  first, and the half checks behave the same in their gates.
