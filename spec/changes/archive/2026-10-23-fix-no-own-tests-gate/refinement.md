# Refinement: fix-no-own-tests-gate

## Problem

When the test and code halves of implement disagree, the suite fails until
review sorts it out. The gates let that through only for a change with `@ac`
tests of its own; for a change without them (every `skip-specs` change,
whose tests carry no tags), a failing suite blocks the design and code
gates, so the change can neither `start review` nor re-enter `implement`
for the next cycle. Found while building a skip-specs change: the reviewer
had to gate review without moving the phase.

## Context

**Observed:**
- `has_own_ac_tests` (`src/specworks/workflow/checks.py:261`) recognises the
  change's tests only by `@ac` tags with the change's criterion IDs.
- `code_tests_pass` (`checks.py:276`, REQ-FLOW-008) and `existing_tests_pass`
  (`src/specworks/workflow/gate.py:117`, REQ-FLOW-006) make a failing suite a
  warning only when `has_own_ac_tests` is true; otherwise it blocks.
- `specworks start review` runs gate test and gate code; `start implement`
  from review runs gate design (REQ-FLOW-014).
- The review gate is not affected: with `--allow-open` and an open finding a
  failing suite is already a warning (REQ-FLOW-011).
- `specworks review` already computes the files changed since the change
  started (committed, uncommitted and untracked) and which of them are tests
  (`src/specworks/workflow/review.py:130-139`, `ctx.report`); without git the
  set is unknown (`report.changed is None`).

**Assumed:**
- A failing suite in a change that changed test files is, in practice, those
  tests meeting the code, not a regression; review still blocks on it.

## Constraints

- [hard] A failing suite still blocks when the change has no tests of its
  own: the design gate's and the code half's regression check stay.
- [hard] No git, or no diff, means no changed files are known: block as today.
- [hard] The review gate blocks on the whole suite as today (outside
  `--allow-open` with an open finding).
- [soft] Reuse the changed-file set `specworks review` computes; no second
  diff.

## Options

### Option A: Changed test files count as the change's own

A failing suite is a warning in the design and code gates when the change
has `@ac` tests of its own or test files changed since it started.

- **Pros:** covers skip-specs and untagged tests; in a parallel build the
  code half still gets a blocking regression check (the test half's tests
  are in its worktree until the merge), and the gates relax only once the
  halves meet.
- **Cons:** a branch that changes test files for another reason also gets a
  warning; needs git.
- **Effort:** S
- **Touches:** `workflow` (REQ-FLOW-006, REQ-FLOW-008)

### Option B: No blocking suite for a skip-specs change

The design and code gates never block on the suite for a skip-specs change.

- **Pros:** simplest.
- **Cons:** a blanket exemption; a real regression surfaces only at review.
- **Effort:** S
- **Touches:** `workflow` (REQ-FLOW-006, REQ-FLOW-008)

### Option C: Skill-only workaround

The build moves the change with `specworks phase` (unchecked) when the
halves disagree.

- **Pros:** no CLI change.
- **Cons:** the coordinator bypasses the gates, which the skills forbid.
- **Effort:** S
- **Touches:** the build skill only

## Recommendation

Option A, agreed with the user: the design and code gates treat a failing
suite as a warning when the change has `@ac` tests of its own or test files
changed since it started; otherwise it blocks, and without git it blocks.

## Open Questions

- A branch that changes test files for unrelated reasons also gets the
  warning at design and code. Accepted for now: review still blocks on the
  whole suite. (who can answer: user, if it turns out to matter)

## Candidate Capabilities

- `workflow`: modified - REQ-FLOW-006 (gate design) and REQ-FLOW-008 (gate
  code): what counts as the change's own tests.
