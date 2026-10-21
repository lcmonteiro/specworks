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

Proposed: waiting for the user's agreement

- `src/specworks/core/changes.py`: `PHASES = ("refine", "specify", "design",
  "implement", "review", "validate", "close", "done")` (**BREAKING**: `test`
  and `code` are no longer phases); `HALVES = ("test", "code")` (new);
  `_read_change` reads a half as `implement`; `set_phase(change, phase)`
  raises `ChangeError` naming `implement` for a half (REQ-PROJ-011)
- `src/specworks/specs/tasks.py`: `Task.half: str = ""` (new field: `"test"`,
  `"code"` or `""`, from a leading `[test]`/`[code]` in any case, which stays
  in `text`); `Task.to_dict()` gains `"half"` (REQ-SPECS-009)
- `src/specworks/specs/check.py`: no new API; `check_change` adds a warning
  naming the half (`[test]` or `[code]`) that has no task (REQ-SPECS-009)
- `src/specworks/workflow/checks.py`: `half_tasks_done(half: str) -> CheckFn`
  (new: every task of that half done, listing only its open tasks);
  `code_tests_pass(ctx) -> Check` (new: `tests_pass`, a warning while the
  change has `@ac` tests of its own); `review_tests_pass(ctx) -> Check` (new:
  `tests_pass`, a warning under `--allow-open` with an open finding).
  `tasks_done` and `tests_pass` are unchanged (validate keeps them)
  (REQ-FLOW-007, REQ-FLOW-008, REQ-FLOW-011)
- `src/specworks/workflow/gate.py`: `GATE_CHECKS["test"]` gains
  `half_tasks_done("test")`; `GATE_CHECKS["code"]` uses
  `half_tasks_done("code")` and `code_tests_pass`, without `acs_have_tests`;
  `GATE_CHECKS["review"]` uses `review_tests_pass`; `GATES` gains `implement`;
  `run_gate(ctx, "implement")` returns the test gate's checks then (once it
  passes) the code gate's, each name prefixed `test: ` / `code: `;
  `gates_to_start(current, phase)` puts `test`, `code` where implement's gate
  goes and raises `GateError` naming `implement` for a half (REQ-FLOW-007,
  REQ-FLOW-008, REQ-FLOW-011, REQ-FLOW-014)
- `src/specworks/workflow/review.py`: `FINDING_STEPS = ("specify", "design",
  "implement", "test", "code", "review")` (new, replacing `FINDING_PHASES`);
  `Finding.phase` holds the step; `BACK_RE`/`DONE_RE` accept `implement`;
  `TYPE_PHASE` unchanged (REQ-FLOW-010)
- `src/specworks/workflow/cycle.py`: `next_cycle(change) -> dict`, same keys
  (`reviewed`, `open`, `startAt`, `phases`, `handOver`); `startAt` is
  `design`, `implement`, `review`, `specify` or None, and `phases` lists steps
  from `design`, `test`, `code`, `review` (REQ-FLOW-012)
- `src/specworks/workflow/artifacts.py`: `half_progress(change: Change) ->
  dict[str, dict[str, int]] | None` (new: `{"test": {"done": 3, "total": 3},
  "code": {"done": 1, "total": 4}}` in implement, else None);
  `src/specworks/cli/changes.py`: `status` adds `halves` to its JSON and a
  `test 3/3, code 1/4` line to its text when not None (REQ-FLOW-001)
- `src/specworks/cli/changes.py`, `src/specworks/cli/workflow.py`: help texts
  of `phase`, `start` and `gate` list the new phases and `gate implement`
  (from `PHASES` and `GATES`) (REQ-FLOW-014)

Stubs: the new names exist with "not implemented" bodies, and are not wired
into the gates, `status` or the phase list yet, so the existing suite stays
green; `PHASES`, `FINDING_PHASES` and the gates' check lists change in the
code phase, together with the existing tests that use `test`/`code` as phases.
`Task.half` is a field that stays `""` until the code phase reads the marker.

Decisions to agree:
- `half_tasks_done`, `code_tests_pass` and `review_tests_pass` are new checks
  instead of giving `tasks_done`/`tests_pass` parameters: validate keeps its
  "every task" and blocking suite checks unchanged.
- `gate implement` reports one list of checks, names prefixed by the half, and
  skips the code gate when the test gate fails (as `start` does).

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
