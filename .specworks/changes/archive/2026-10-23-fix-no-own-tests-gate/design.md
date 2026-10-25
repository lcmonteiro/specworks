# Design: fix-no-own-tests-gate

## Context

See proposal.md. `has_own_ac_tests` (`src/specworks/workflow/checks.py`)
decides whether a failing suite only warns in the design gate
(`existing_tests_pass`, `src/specworks/workflow/gate.py`) and the code gate
(`code_tests_pass`). `GateContext.report` already holds the files changed
since the change started (`ReviewReport.changed`, `None` without git), each
with its kind (`source`, `test`, `other`, `deleted`).

## Goals / Non-Goals

**Goals:**
- One rule for "the change has tests of its own", used by both gates, that
  also counts changed test files.

**Non-Goals:**
- Any change to the review gate, validate, or how `specworks review`
  computes the changed files.

## Decisions

### Changed test files come from `ctx.report` (REQ-FLOW-006, REQ-FLOW-008)

The new rule reads `ctx.report.changed` and counts files of kind `test`
(deleted test files do not count). It reuses the diff `specworks review`
computes against the change's start, so the gates and review agree on what
changed. `None` (no git, or the diff cannot be computed) counts as no
changed test files, so the suite blocks as today. Alternative: a second,
lighter `git diff` in the gates; rejected, two answers to "what changed".

### One helper that also says why (REQ-FLOW-006, REQ-FLOW-008)

`own_tests(ctx) -> str | None` returns the reason the change has tests of its
own (`"this change has @ac tests of its own"` or `"this change has changed
test files"`), or `None`. Both gates pass that reason to `not_blocking`, so
the warning says which case applies. `has_own_ac_tests` stays as the first
half of the rule.

## Interfaces

Agreed with the user

- `src/specworks/workflow/checks.py`: `own_tests(ctx: GateContext) -> str |
  None` (new: why the change has tests of its own, or None) (REQ-FLOW-006,
  REQ-FLOW-008); `code_tests_pass` uses it (REQ-FLOW-008)
- `src/specworks/workflow/gate.py`: `existing_tests_pass` uses it
  (REQ-FLOW-006)

Nothing breaks: `has_own_ac_tests` keeps its signature and callers, and no
CLI command, option or JSON shape changes. The gates' warning text names the
reason `own_tests` returns, so tests can assert `@ac tests` or `changed test
files` in it.

## Risks / Trade-offs

- [The design and code gates now compute the changed files (a git diff)] ->
  only when the suite fails, since the rule is read after the run; the
  report is cached on the context.
- [Test edits unrelated to the change relax the two gates] -> accepted;
  review still blocks on the whole suite.

## Open Questions

None.
