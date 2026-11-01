# Proposal: fix-commit-after-close

## Why

The close and done skills commit with `specworks commit` after `specworks
close`, but close has already archived the change and `commit` finds only
active changes, so every close fails at its commit. `alreadyDirty` also
flags the change's own files. The refinement chose Option A: `commit` falls
back to the archived change.

## What Changes

- `specworks commit --change <ref>` uses the active change of that name or,
  when there is none, the newest archived one (`archived_as`); an archived
  change's default subject is `<ref>: close`.
- `alreadyDirty` leaves out the files of the change's own folder; they are
  still committed.
- Assumption: the newest archived change with the name is the one close just
  archived.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `project`: REQ-PROJ-024 (an archived change; the already-dirty list), with
  AC-PROJ-024.6 and AC-PROJ-024.7.
- `cli`: REQ-CLI-012 (an archived change), with AC-CLI-012.4; AC-CLI-012.3
  now names neither active nor archived.

## Impact

- `src/specworks/core/changes.py` (`commit_phase`),
  `src/specworks/cli/changes.py` (`commit`), `tests/test_commit.py`. No skill
  change: the close and done skills already say to run `specworks commit`.

## Out of Scope

- Committing an older archived change on purpose.
