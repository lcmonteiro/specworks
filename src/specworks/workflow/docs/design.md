# Design: workflow

## Overview

The workflow a change goes through,
`refine → specify → design → test → code → review → validate → close`, as far as
the CLI can check it. The phase skills do the work that needs judgement; this
capability gives them facts and gates.
- **Artifacts** (`artifacts.py`): the artifact graph from the packaged
  `schema.yaml` (what each phase writes and what it requires), each artifact's
  state, and the instructions and template for writing it.
- **Checks** (`checks.py`): every check defined once, as a function of a
  `GateContext` that computes what it reads (analysis, review report, review.md)
  on first use.
- **Gates** (`gate.py`): each phase's list of checks, and `start`, which runs
  the gates a phase depends on before moving the change.
- **Review** (`review.py`): the drift report (changed files against the base
  branch, untagged code and tests) and the parser for review.md.
- **Cycles** (`cycle.py`): where the next design → test → code → review cycle
  starts after a review.
- **Validate** (`validate.py`): the grouped, read-only final report.

## Decisions

### Gates only check what the CLI can see

The gates look at specs, tasks, tags, review.md, git and the project's own
commands. Anything that needs judgement (whether a test fails for the right
reason, whether the code matches the spec's intent) stays with the skills.
(baseline-workflow)

### One definition per check, shared by gates and validate

Gates and validate are lists of the same check functions. Validate adds a
group and the phase skill that fixes each failure, and `start` prints that fix
too. A check returns `None` when it doesn't apply. Warnings
(`blocking=False`) never fail a gate. (baseline-workflow)

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
`back to <phase>:`, fails the review gate and validate, even inside a build.
A finding the parser misses would otherwise let a gate pass with it still open.
(baseline-workflow)

### Build cycles start at the earliest phase a finding needs

Each finding is routed by its type, by `back to <phase>:`, or past a
`done in <phase>:`. A spec finding hands over to specify instead of starting a
cycle. (baseline-workflow)

## Interfaces

- `src/specworks/workflow/artifacts.py`: `load_artifacts()`,
  `artifact_states(change)`, `instructions(ws, module, change, artifact_id)`.
- `src/specworks/workflow/checks.py`: `Check`, `GateContext`, `passed(checks)`,
  `run_checks(ctx, checks)`, and the check functions.
- `src/specworks/workflow/gate.py`: `GATE_CHECKS`, `GATES`,
  `run_gate(ctx, phase)`, `gates_to_start(current, phase)`,
  `start_phase(ctx, phase)`.
- `src/specworks/workflow/review.py`: `review_change(analysis, base)`,
  `changed_paths(ws, since)`, `deleted_paths(ws, since)`, `ChangedFile` (`kind`, `was`),
  `ReviewReport`, `parse_review(text)`, `read_review(change)`, `ReviewDoc`,
  `Finding`.
- `src/specworks/workflow/cycle.py`: `next_cycle(change)`.
- `src/specworks/workflow/validate.py`: `validate_change(ctx)`,
  `summary(checks)`.

## Constraints

- Validate and the gates write nothing to the project. Only `start` writes, to
  the change's metadata.
- Built on `project` (config, workspace, changes, runner) and `specs` (specs,
  tags, trace).
