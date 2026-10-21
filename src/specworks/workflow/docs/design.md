# Design: workflow

## Overview

The workflow a change goes through,
`refine → specify → design → implement (test | code) → review → validate → close`, as far as
the CLI can check it. The phase skills do the work that needs judgement; this
capability gives them facts and gates.
- **Artifacts** (`artifacts.py`): the artifact graph from the packaged
  `schema.yaml` (what each phase writes and what it requires), each artifact's
  state, the instructions and template for writing it, and each half's task
  progress in implement.
- **Checks** (`checks.py`): every check defined once, as a function of a
  `GateContext` that computes what it reads (analysis, review report, review.md)
  on first use.
- **Gates** (`gate.py`): each phase's (and each half's) list of checks, and
  `start`, which runs the gates a phase depends on before moving the change.
- **Review** (`review.py`): the drift report (changed files against the base
  branch, untagged code and tests) and the parser for review.md.
- **Cycles** (`cycle.py`): which steps the next build cycle runs after a
  review.
- **Validate** (`validate.py`): the grouped, read-only final report.

## Decisions

### Gates only check what the CLI can see

The gates look at specs, tasks, tags, review.md, git and the project's own
commands. Anything that needs judgement (whether a test fails for the right
reason, whether the code matches the spec's intent) stays with the skills.
(baseline-workflow)

### A change's interfaces live in its own module

The design gate counts a file named under Interfaces only when it exists inside
the change's module folder. The path may be written relative to the module or
to the workspace root, the form every CLI path is printed in. A same-named file
elsewhere in the workspace must not stand in for a missing stub, and work
across modules belongs to a change at the top level or in the lowest common
module. (module-interface-paths)

### One definition per check, shared by gates and validate

Gates and validate are lists of the same check functions. Validate adds a
group and the phase skill that fixes each failure, and `start` prints that fix
too. A check returns `None` when it doesn't apply. Warnings
(`blocking=False`) never fail a gate. (baseline-workflow)

### Implement's halves are gated separately

`implement` has two halves that run in parallel, each reading only the
project, refinement, specs and design: the test half and the code half.
`gate test` and `gate code` each check one half (its `[test]` or `[code]`
tasks); `gate implement` runs the test gate, then the code gate once the test
gate passes, with each check named `test: ` or `code: `. `start` treats
implement's gate as both, so leaving implement needs both halves; going back
to implement needs only the design gate. The half checks are new functions
(`half_tasks_done`, `code_tests_pass`, `review_tests_pass`) rather than
parameters on `tasks_done`/`tests_pass`, so validate keeps its "every task"
and blocking-suite checks unchanged. (parallel-test-code)

### The code gate does not wait for the tests

The code half is written without reading the change's tests, so the code gate
no longer needs an `@ac` test per criterion, and a failing suite only warns
once the change has `@ac` tests of its own (review runs them). For a change
that only modifies requirements, those include the tests that existed before
it: they encode the old behaviour and are expected to fail until the test half
updates them, and the gate can't tell them from unrelated tests, so it
accepts that; the review gate runs the whole suite and blocks on it, except as
a warning under `--allow-open` while review.md has an open finding.
(parallel-test-code)

### Specs are fingerprinted when they are agreed

Leaving specify through `start` records a fingerprint of each requirement.
Later gates warn, without blocking, when the specs drift from that agreement,
and starting design again accepts the new specs. (baseline-workflow)

### Deleted code is reviewed like changed code

The drift report lists files deleted on the branch (kind `deleted`, with the
kind they had). Deleted source and test files must be accounted for in
review.md, like untagged changed files, because the trace only checks the
change's own requirements: a deletion is where another requirement can silently
lose its code. Detecting that loss automatically (reading the deleted file's
tags at the base) was left for later. (review-deleted-files)

### review.md is parsed strictly

A checkbox the parser can't read, or an open finding with no known type or
`back to <step>:`, fails the review gate and validate, even inside a build.
A finding the parser misses would otherwise let a gate pass with it still open.
The same goes for any checkbox outside a finding, at the top level or indented
under another bullet: only sub-steps inside a finding's block are allowed, so
open work can't hide behind indentation. (baseline-workflow, review-indented-checkboxes)

### Build cycles run only the steps the findings need

A finding's route is a step: `specify, design, implement, test, code,
review`. It is set by its type, by `back to <step>:` (`implement` means both
halves), or past a `done in <step>:` (specify → design, design → implement,
implement, test or code → review). `next_cycle` keeps its keys; its `phases`
lists the steps to run: code half and review, test half and review, both
halves and review, or design, both halves and review. A spec finding hands
over to specify instead of starting a cycle. Re-running every phase after the
earliest finding was replaced: a code finding no longer re-runs the tests.
(baseline-workflow, parallel-test-code)

## Interfaces

- `src/specworks/workflow/artifacts.py`: `load_artifacts()`,
  `artifact_states(change)`, `instructions(ws, module, change, artifact_id)`,
  `half_progress(change)` (`{"test": {"done", "total"}, "code": {...}}` in
  implement, else None; `status` shows it as `test 3/3, code 1/4`).
- `src/specworks/workflow/checks.py`: `Check`, `GateContext`, `passed(checks)`,
  `run_checks(ctx, checks)`, and the check functions (including
  `half_tasks_done(half)`, `code_tests_pass`, `review_tests_pass`).
- `src/specworks/workflow/gate.py`: `GATE_CHECKS`, `GATES` (with `test`,
  `code` and `implement`), `run_gate(ctx, phase)`, `gates_to_start(current, phase)`,
  `start_phase(ctx, phase)`.
- `src/specworks/workflow/review.py`: `review_change(analysis, base)`,
  `changed_paths(ws, since)`, `deleted_paths(ws, since)`, `ChangedFile` (`kind`, `was`),
  `ReviewReport`, `parse_review(text)`, `read_review(change)`, `ReviewDoc`,
  `Finding` (`phase` holds its step), `FINDING_STEPS`.
- `src/specworks/workflow/cycle.py`: `next_cycle(change)` (`reviewed`, `open`,
  `startAt`, `phases`, `handOver`; `phases` lists steps).
- `src/specworks/workflow/validate.py`: `validate_change(ctx)`,
  `summary(checks)`.

## Constraints

- Validate and the gates write nothing to the project. Only `start` writes, to
  the change's metadata.
- Built on `project` (config, workspace, changes, runner) and `specs` (specs,
  tags, trace).
