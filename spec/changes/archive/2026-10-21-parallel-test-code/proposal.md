# Proposal: parallel-test-code

## Why

Code is written to make the test phase's tests pass, so tests and code share
one reading of the spec, code waits for test, and a review cycle re-runs every
phase after the earliest finding. The refinement chose Option A: one
`implement` phase whose test and code halves run in parallel, each depending
only on the project, refinement, specs and design, and a review that decides
the next step per finding.

## What Changes

- **BREAKING** The phases become refine, specify, design, implement, review,
  validate, close, done. `test` and `code` are no longer phases but the two
  halves of `implement`. A `.change.yaml` saved in `test` or `code` is read as
  `implement`; `specworks phase` and `specworks start` refuse `test` and `code`,
  naming `implement`.
- `specworks gate test` and `specworks gate code` check one half each; the
  new `specworks gate implement` runs both. Moving on from implement (to
  review and later) needs both halves' gates.
- Tasks carry their half: `- [ ] 1.2 [test] …` and `- [ ] 1.3 [code] …`
  (a task with no marker belongs to design). `gate test` needs the `[test]`
  tasks done and `gate code` the `[code]` tasks. `specworks check` warns when
  a change with criteria has no `[test]` task, or one with requirements has no
  `[code]` task.
- `gate code` no longer needs an `@ac` test for every criterion. A failing
  suite blocks it only while the change has no `@ac` tests of its own;
  otherwise it is a warning, and review runs the suite.
- `specworks status` shows each half's task progress while a change is in
  implement (`test 3/3, code 1/4`).
- Review findings route to a half: `back to test:` or `back to code:` (and the
  types that belong to each); `back to implement:` routes to both. After
  `done in design:` a finding needs both halves; after `done in test:` or
  `done in code:` it needs review.
- `specworks cycle` returns the steps the open findings need instead of every
  phase after the earliest: code half and review; test half and review; both
  halves; design then both halves; or specify.
- Skills: build runs the test half in its own git worktree (only design's
  stubs) in parallel with the code half, merges the worktree back (keeping
  every tick on a `tasks.md` conflict), then runs review; without a worktree,
  the test half first, then the code half. Test, code and review describe
  their half or their new checks; the tasks instruction asks for the markers.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `project`: REQ-PROJ-011 (the phase list, and old `test`/`code` values).
- `specs`: REQ-SPECS-009 (the half marker on tasks, and the check's warnings).
- `workflow`: REQ-FLOW-001 (status shows the halves), REQ-FLOW-007 (gate
  test, the test half), REQ-FLOW-008 (gate code, the code half),
  REQ-FLOW-010 (routing findings to halves), REQ-FLOW-011 (gate review: the
  tag and test checks named, a failing suite only warns with open findings
  under `--allow-open`), REQ-FLOW-012 (build cycles by step), REQ-FLOW-014
  (starting a phase; `gate implement`).

## Impact

- `src/specworks/core/changes.py` (PHASES, reading old phases),
  `src/specworks/specs` (task parsing and check), `src/specworks/workflow`
  (gate, cycle, review, artifacts/status), `src/specworks/cli` (phase, start,
  gate, status help and output), `src/specworks/schema.yaml` (tasks
  instruction).
- Skills build, test, code, review, the shared phase-subagents text, and
  their installed copies.
- Existing tests that use the phases `test` and `code`.

## Out of Scope

- A change in two phases at once (Option B).
- Isolation for the code half: it works in the main checkout.
- Hand-run `/specworks-test` and `/specworks-code` choosing a worktree: only
  the build runs the halves in parallel.
- `status` running the gates.
