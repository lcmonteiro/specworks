# Proposal: fix-no-own-tests-gate

## Why

A change with no `@ac` tests of its own (every skip-specs change) gets stuck
in implement when the test and code halves disagree: a failing suite blocks
the design and code gates, so it can neither `start review` nor re-enter
implement. The refinement chose to count test files changed since the change
started as the change's own tests.

## What Changes

- The design gate and the code gate treat a failing suite as a warning when
  the change has tests of its own: `@ac` tests tagged with its criteria (as
  today) or test files changed since the change started (committed,
  uncommitted or untracked, the set `specworks review` reports). The warning
  says which applies.
- Otherwise a failing suite blocks as today. Without git, or when the changed
  files cannot be computed, no changed test files are known, so it blocks.
- The review gate is unchanged.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `workflow`: REQ-FLOW-006 (gate design: the existing tests) and
  REQ-FLOW-008 (gate code: the change's own tests failing).

## Impact

- `src/specworks/workflow/checks.py` (`has_own_ac_tests` or a new helper
  beside it, `code_tests_pass`) and `src/specworks/workflow/gate.py`
  (`existing_tests_pass`); their tests.
- No CLI surface, option or data change.

## Out of Scope

- The review gate (already a warning under `--allow-open` with an open
  finding).
- Telling apart test files changed for this change from other test edits on
  the branch.
- The skill gaps found in the same build (design's `Proposed:` line, the
  worktree base, the review "finish" run, `.gitignore`).
