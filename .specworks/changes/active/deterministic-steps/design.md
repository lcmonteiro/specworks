# Design: deterministic-steps

## Context

See proposal.md. `_check_tasks` in `src/specworks/specs/check.py` already
reads every task with its `num`, `half` and line, and already warns about a
missing half (REQ-SPECS-009). The skills and instructions are text checked
by wording tests in `tests/test_skills.py`.

## Goals / Non-Goals

**Goals:**
- One more pass in `_check_tasks`, on the task text alone.
- The change follows its own rule: its `[code]` tasks are verified without
  the test half, and its wording is pinned below.

**Non-Goals:**
- Parsing what a task means; only task numbers of the change and the literal
  `specworks run test` count.
- Checking that pinned phrases appear (Option C).

## Decisions

### Match task numbers against the change's own `[test]` tasks

A `[code]` task warns when its text contains, as a whole token, the number
of a `[test]` task of the same change (`1.1`, not `11.1` or `3.11`), or the
literal `specworks run test`. Matching only real `[test]` numbers keeps
version numbers and references to `[code]` or no-half tasks silent.
Alternative rejected: a list of phrases such as "the tests pass", which is
fuzzy and fires on ordinary wording. Serves REQ-SPECS-015.

### Pinned wording

Both halves use these phrases verbatim; the wording tests assert them and
the text contains them.

- Warning for a named `[test]` task: `task <code num> [code] names task <test num> [test]: the code half cannot see the test half's tests until the merge; verify it with lint, typecheck or observable behaviour`
- Warning for the suite: `task <num> [code] requires the suite (specworks run test): the suite runs in gate implement after the merge; verify it with lint, typecheck or observable behaviour`
- Tasks instruction (`schema.yaml`): `A [code] task is verified by lint, typecheck or observable behaviour, never by the test half's tests or the suite`
- Design instruction (`schema.yaml`): `**Pinned wording**`
- Code skill: `Tick a [code] task when its own checks pass; the suite is not one of them`
- Code skill: `Write the pinned phrases of design.md verbatim`
- Test skill: `Assert only the pinned phrases of design.md, verbatim`

## Interfaces

None: the warning is a new pass inside `_check_tasks`; no public function,
CLI command or data shape changes.

## Diagrams

No structural change.

## Risks / Trade-offs

- [A `[code]` task legitimately mentions a `[test]` task] -> it is a
  warning, never an error, and the task can be reworded.
