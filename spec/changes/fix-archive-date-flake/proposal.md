# Proposal: fix-archive-date-flake

## Why

`tests/test_archive.py` builds `ARCHIVED` from `date.today()` when the module
is imported, while the code under test reads the date when a change is
archived. A run that crosses midnight between the two fails: it was seen once
and did not reproduce.

## What Changes

- `tests/test_archive.py` pins the date the archive code reads to a fixed
  `TODAY` with an autouse fixture, and builds `ARCHIVED` from it.

## Capabilities

None: only a test changes, and the behaviour is the same. The change is marked
`skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- `tests/test_archive.py` only. No source, CLI or data change.

## Out of Scope

- Other tests that call `date.today()` inside a single test body; they cannot
  see a stale import-time value.
