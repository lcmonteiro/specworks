# Proposal: docs-active-path

## Why

`active-changes-dir` moved the changes in flight to `spec/changes/active/`. `CLAUDE.md` and `README.md` still name `spec/changes/`.

## What Changes

- `CLAUDE.md` says `spec/changes/active/` holds the work in flight.
- The `init` line of `README.md` lists `spec/changes/active/` and `spec/changes/archive/`.

## Capabilities

None: only text changes. The change is marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- `CLAUDE.md` and `README.md` only.

## Out of Scope

- The GitHub wiki, which is a separate repository.
