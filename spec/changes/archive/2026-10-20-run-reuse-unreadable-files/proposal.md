# Proposal: run-reuse-unreadable-files

## Why

Gates, validate and close crash with a traceback while fingerprinting the
working tree when an untracked file's name isn't valid UTF-8 (reproduced), or
when an untracked file can't be read. Every gate is then blocked, even though
the tests pass (suspected bug 3 of `baseline-project`; refinement.md, option B).

## What Changes

- Untracked file names are taken as the raw bytes git reports, so a name that
  isn't valid UTF-8 is fingerprinted like any other, and reuse keeps working.
- An untracked file that can't be read turns reuse off for that run: the command
  runs for real, with no crash and no stale result.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: REQ-PROJ-014 "Reusing command results" MODIFIED. Its description
  adds "an untracked file that cannot be read" to the cases where reuse is off,
  and it gets two new criteria (AC-PROJ-014.7, AC-PROJ-014.8).

## Impact

`src/specworks/core/runner.py` (`tree_fingerprint`) and
`tests/test_run_cache.py`. No API, data, config or dependency change.

## Out of Scope

- Hashing unreadable files by size and modification time (option C: could
  reuse a stale result).
- Git-ignored files, which the fingerprint never sees (`specworks run`
  already covers them).
