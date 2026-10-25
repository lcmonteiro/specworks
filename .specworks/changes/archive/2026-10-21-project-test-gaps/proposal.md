# Proposal: project-test-gaps

## Why

Two behaviours of `project` that its living spec states have no test that would
fail if they broke, found when `baseline-project` was validated: `dark_theme:
none` being accepted (AC-PROJ-003.5 is tagged only on tests of rejected
values), and archived changes listed oldest first (REQ-PROJ-012's only test has
one archived change, and no criterion states the order).

## What Changes

- No behaviour change: a criterion for the archive order, and tests for it and
  for `dark_theme: none`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: REQ-PROJ-012 "Archived changes" MODIFIED, with a new criterion
  AC-PROJ-012.2 for the order. AC-PROJ-003.5 is unchanged and gets its test.

## Impact

`tests/test_archive.py` and `tests/test_diagrams.py` (or `tests/test_cli.py`).
No code change.

## Out of Scope

- Archived changes closed on the same day are listed by name, not by close
  time, since the folder holds only the date. A candidate for its own change if
  that order matters.
