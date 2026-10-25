# Refinement: parallel-test-code

## Problem

The code phase writes code until the test phase's tests pass, so tests and
code share one reading of the spec: a test that misreads a criterion gets
code that implements the misreading, and the suite is green. The user wants
"test step and code step [to] run in parallel with same dependencies:
refine, spec, design, project", and "the review phase [to] run the tests,
review the code, and test against spec", and from that result to "decide
for each step [where] we should go next". Code also waits for test, and
every review cycle re-runs every phase after the earliest finding.

## Context

**Observed:**
- A change has one phase from a fixed list (`PHASES` in
  `src/specworks/core/changes.py`: refine, specify, design, test, code,
  review, validate, close, done). Capability `project`.
- `specworks start <phase>` runs the gates of the phases left behind
  (`gates_to_start` in `src/specworks/workflow/gate.py`, REQ-FLOW-014), so
  `start code` needs `gate test`.
- `gate test` (REQ-FLOW-007) needs an `@ac` test for every criterion;
  `gate code` (REQ-FLOW-008) needs every task done, `@req` code, an `@ac`
  test for every criterion and a passing suite.
- `specworks cycle` (`src/specworks/workflow/cycle.py`, REQ-FLOW-012) starts
  the next cycle at the earliest phase any open finding needs and runs every
  later phase: a test finding re-runs test, code and review.
- The test skill runs the new tests against design's stubs and requires them
  to fail for the right reason; the code skill makes them pass task by task.
- `/specworks-build` runs each phase in a subagent (`_shared/phase-subagents.md`).
  Claude Code subagents can run in their own git worktree.

**Assumed:**
- Test files and code files of a change do not overlap, so merging the test
  half's worktree back is normally trivial.
- Copilot has no worktree isolation for subagents.

## Constraints

- [hard] Test and code each depend only on the project, refinement, specs
  and design, never on each other.
- [hard] A change still has exactly one phase at a time.
- [hard] The new tests still have to fail for the right reason against the
  stubs before they meet the code.
- [hard] Every finding's next step is decided with the user, as today.
- [soft] Where no worktree is available, fall back to the test half first
  (tests written and red), then the code half, in one checkout.
- [soft] Keep the existing phase names working where users see them
  (`back to test:`, `back to code:`).

## Options

Agreed with the user: test and code run in parallel and review decides the
next step per finding (keeping test → code with only per-step cycles was
considered and left out). The options below are how the CLI models the
parallel phases.

### Option A: One `implement` phase holding both halves

`design → implement → review`. In implement, the test half (in a worktree
with design's stubs) and the code half (in the main checkout, running only
the existing tests) run in parallel; `gate test` and `gate code` check each
half, and `start review` needs both.

- **Pros:** one phase per change; status, list, start and close keep their
  logic; each half keeps its own gate.
- **Cons:** renames phases users see; `status` needs to show the halves;
  changes in `test` or `code` today need moving to `implement`.
- **Effort:** M
- **Touches:** `project` (phase list), `workflow` (REQ-FLOW-007, 008, 012, 014), the build, test, code and review skills

### Option B: A change can be in test and code at once

The phase becomes a set (`{test, code}`, `{test}`, `{code}`).

- **Pros:** closest to the picture; phase names unchanged.
- **Cons:** every command reading the phase changes; new rules for moving
  one member of the set; the most requirements touched.
- **Effort:** L
- **Touches:** `project`, `workflow`, `cli`, every phase skill

### Option C: Keep `test → code`, drop code's dependency on the tests

`start code` needs only the design gate; the skills run both in parallel.

- **Pros:** smallest change; nothing renamed.
- **Cons:** the recorded phase is wrong while both run; nothing in the CLI
  knows "both halves done".
- **Effort:** S
- **Touches:** `workflow` (REQ-FLOW-008, 012, 014), the skills

## Recommendation

Option A, agreed with the user, with these parts:
- The test half works in its own git worktree with only design's stubs, so
  its tests still fail for the right reason; the coordinator merges it back
  before review. The code half runs the existing suite as its regression
  check, without this change's tests.
- `gate code` no longer needs this change's tests; `start review` needs both
  halves' gates.
- Review runs the whole suite, reads the code against the spec and design,
  and reads each test against its criterion. A failing test becomes a
  finding: code wrong, test wrong, or spec unclear.
- `cycle` returns the steps the open findings need: code half and review;
  test half and review; both halves in parallel; design then both halves;
  or specify.
- Without a worktree: the test half first (tests red), then the code half.

## Open Questions

- How `status` shows the two halves of implement (done / in progress per
  half). (who can answer: user, in specify)
- How a change in `test` or `code` today moves to `implement`, and whether
  `specworks phase test|code` stay as names for the halves. (who can answer:
  user, in specify)
- How `tasks.md` marks which tasks belong to which half. (who can answer:
  user, in specify)

## Candidate Capabilities

- `workflow`: modified - the implement phase, gates test and code as its
  halves, starting review, build cycles per finding (REQ-FLOW-007, 008,
  012, 014).
- `project`: modified - the phase list.
