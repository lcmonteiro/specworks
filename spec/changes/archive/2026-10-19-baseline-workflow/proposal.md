# Proposal: baseline-workflow

## Why

Record the existing behaviour of `workflow` (`src/specworks/workflow`): a
change's artifacts and instructions, the phase gates, starting a phase, the
review drift report and review.md, build cycles, and validate. Later changes can
then MODIFY these requirements instead of only ADDING them.

## What Changes

- No behaviour change. The behaviour `workflow` already has is written down as
  requirements, and the existing tests and code are tagged with `@ac` / `@req`.
- One new test covers a criterion that no test checks yet: instructions for an
  unknown artifact are refused.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workflow`: its first requirements, REQ-FLOW-001 to REQ-FLOW-014.

## Impact

Comment tags in `src/specworks/workflow/*.py` and in the tests that check these
behaviours (`tests/test_cli.py`, `test_modules.py`, `test_propose.py`,
`test_specified.py`, `test_design_phase.py`, `test_test_phase.py`,
`test_code_phase.py`, `test_review_phase.py`, `test_build_cycle.py`,
`test_validate_phase.py`, `test_start_phase.py`, `test_run_cache.py`), plus one
new test. No API, data or dependency change.

The tag scan itself belongs to `specs`, and the command surface (`--json`,
error output, resolving a change reference) to `cli`.

## Out of Scope

Suspected bugs and unclear behaviour found while reading the code. Each one is a
candidate for its own change:

- **Deleted files are never among a review's changed files.** `changed_paths`
  keeps only files that still exist, so removing untagged code needs no
  accounting in review.md. That may be intended, but it isn't stated anywhere.
- **The design gate also accepts an Interfaces file at the workspace root.**
  A path named under Interfaces counts as existing when it exists relative to
  the module or to the workspace root. Inside a module, a same-named file at the
  top level would satisfy the check.
- **An indented checkbox outside any finding is ignored silently.** In
  review.md, a top-level checkbox that is not a finding is reported. An indented
  one under a non-finding bullet is neither parsed nor reported. Indented
  `R<n>` findings are still read.
