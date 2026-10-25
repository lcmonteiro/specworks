# Proposal: module-outside-workspace

## Why

A module whose folder, after following symlinks, is outside the workspace makes
`context` and `module list` crash, and from inside that module the workspace
loads differently (reproduced; found in review R2 of `module-add-nested`;
refinement.md, option A).

## What Changes

- Loading a workspace fails when a module's folder, with symlinks resolved, is
  outside the top level's folder, naming the module, its path and where the
  folder really is. A listed module that isn't checked out but points outside
  is refused too.
- A symlinked module whose target stays inside the workspace keeps loading.
- The nesting check's skip for a module no other module holds (review R2 of
  `module-add-nested`) can no longer happen and is removed with its test.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: REQ-PROJ-006 "Workspace of modules" MODIFIED. Its description says
  a module's folder must be inside the top level's, and it gets a new
  criterion, AC-PROJ-006.9.

## Impact

`src/specworks/core/workspace.py` (`_load_tree`, `_check_nesting`) and
`tests/test_modules.py`. A workspace with a module outside it, which crashes
today, now fails loading with a message. No API, data or dependency change.

## Out of Scope

- Supporting modules outside the workspace (option B).
