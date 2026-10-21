# Design: parallel-test-code

## Context

See proposal.md and refinement.md. Today the phase list is one tuple
(`PHASES` in `src/specworks/core/changes.py`), `start` walks it with
`gates_to_start`, the gates are a dict of check lists (`GATE_CHECKS` in
`src/specworks/workflow/gate.py`), review findings route to one of
`FINDING_PHASES` (`src/specworks/workflow/review.py`) and `next_cycle`
(`src/specworks/workflow/cycle.py`) runs every phase after the earliest.

## Goals / Non-Goals

**Goals:**
- `implement` replaces `test` and `code` as phases; `test` and `code` stay
  as the names of its halves (gates, review routing, cycle steps, task
  markers).
- Each half's gate checks only that half.
- `cycle` returns the steps the findings need.

**Non-Goals:**
- A phase set per change; any change to validate's checks beyond what the
  shared check functions already do.

## Decisions

### `implement` is a phase; `test` and `code` are halves (REQ-PROJ-011, REQ-FLOW-014)

`PHASES` becomes `refine, specify, design, implement, review, validate,
close, done`, plus `HALVES = ("test", "code")`. Reading a `.change.yaml`
whose phase is a half returns `implement` (no rewrite on read; the next
`set_phase` saves `implement`). `set_phase` and `start` refuse a half with
"`test` and `code` are the halves of `implement`". Alternative: aliases that
move the change to implement; rejected with the user (two names for one
phase).

### Gates per half, and `gate implement` (REQ-FLOW-007, 008, 014)

`GATE_CHECKS` keeps `test` and `code` (each with a half-scoped tasks check)
and `GATES` gains `implement`, run as the test gate then the code gate (the
checks of both, the code gate's only after the test gate passes, as in
`start`). `gates_to_start` treats implement's gate as `["test", "code"]`, so
`start review` from implement runs both and stops at the first that fails.
Going back to implement from review needs only the design gate (the phase
before it).

### The code gate's suite (REQ-FLOW-008)

`tests_pass` in the code gate becomes non-blocking when the change has `@ac`
tags of its own in test files (the same test `existing_tests_pass` uses in the
design gate), with a detail line saying review runs them. `acs_have_tests`
leaves the code gate. The review gate lists its checks itself (it already
does in `GATE_CHECKS`); its `tests_pass` becomes non-blocking under
`--allow-open` when review.md has an open finding (REQ-FLOW-011).

### Task halves (REQ-SPECS-009, REQ-FLOW-001)

`Task` gains `half: str` (`"test"`, `"code"` or `""`), read from a leading
`[test]` or `[code]` in its text (any case), which stays in `text`. The
check's new warning lives with the existing task checks in
`src/specworks/specs/check.py`. `status` adds `halves` for a change in
implement, computed from the tasks only.

### Steps instead of phases in review routing and cycles (REQ-FLOW-010, 012)

A finding's `phase` field becomes its step: one of `specify, design,
implement, test, code, review`. `BACK_RE` and `DONE_RE` accept `implement`
too. After `done in <step>`: specify → design, design → implement, and
implement, test or code → review. `next_cycle` keeps its keys (`startAt`,
`phases`, `handOver`) so the build skill reads the same shape; `phases` now
lists the steps (`design`, `test`, `code`, `review`) and `startAt` is a
phase (`design`, `implement`, `review`, or `specify` for the hand-over).

### Skills

Build runs the two halves of implement in parallel: the test half in a
subagent with its own git worktree (Claude Code: `isolation: worktree`),
the code half in the main checkout, then merges the worktree branch back,
keeping every tick when `tasks.md` conflicts. Without worktrees: the test
half, then the code half. The test and code skills start `implement` and
work only on their half's `[test]` / `[code]` tasks and gate; the code skill
no longer reads this change's tests. Review runs the suite, reads the code
and each test against its criterion, and classifies each failing test as a
code, test or spec finding. The tasks instruction in `schema.yaml` asks for
the markers.

## Interfaces

- `src/specworks/core/changes.py`: `PHASES` (implement instead of test,
  code); `HALVES = ("test", "code")`; `_read_change` maps a half to
  `implement`; `set_phase` raises `ChangeError` for a half (REQ-PROJ-011)
- `src/specworks/specs/tasks.py`: `Task.half: str`, in `Task.to_dict()` as
  `"half"` (REQ-SPECS-009)
- `src/specworks/specs/check.py`: warning when a half has no task
  (REQ-SPECS-009)
- `src/specworks/workflow/checks.py`: `tasks_done(half: str | None = None) ->
  CheckFn` (the half's tasks, or every task); `tests_pass` non-blocking with
  own `@ac` tests (code gate) or with open findings under `--allow-open`
  (review gate) (REQ-FLOW-007, 008, 011)
- `src/specworks/workflow/gate.py`: `GATES` with `implement`;
  `gates_to_start` expands implement to `test`, `code` and refuses a half
  (REQ-FLOW-014)
- `src/specworks/workflow/review.py`: `FINDING_STEPS = ("specify", "design",
  "implement", "test", "code", "review")` replacing `FINDING_PHASES`;
  `Finding.phase` holds the step (REQ-FLOW-010)
- `src/specworks/workflow/cycle.py`: `next_cycle(change) -> dict` with the
  same keys; `phases` are steps (REQ-FLOW-012)
- `src/specworks/workflow/artifacts.py`: `half_progress(change) -> dict[str,
  dict[str, int]] | None` (`{"test": {"done": 3, "total": 3}, ...}`);
  `src/specworks/cli/changes.py`: `status` shows it as `halves` (REQ-FLOW-001)
- `src/specworks/cli/changes.py`, `src/specworks/cli/workflow.py`: help
  texts list the new phases and `gate implement`

## Risks / Trade-offs

- [Projects with changes in `test` or `code`] -> read as `implement`; no
  migration step.
- [Merging the test worktree conflicts on tasks.md] -> only ticks differ; the
  build skill keeps every tick.
- [Tasks without markers, written before this change] -> no half: they count
  in validate's "every task is done" but in neither half's gate; `check`
  warns that a half has no task.
- [Code half blind to the tests produces more review findings] -> accepted:
  that disagreement is what the change is for.

## Open Questions

None.
