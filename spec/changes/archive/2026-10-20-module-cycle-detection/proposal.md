# Proposal: module-cycle-detection

## Why

A module whose folder leads back to an ancestor through a symlink makes every
command crash with `RecursionError` (reproduced). A folder listed as a module by
two parents is quietly loaded twice under two names (suspected bug 4 of
`baseline-project`; refinement.md, option B).

## What Changes

- Loading a workspace fails when a module's folder, with symlinks resolved, is
  already part of the workspace: one of its ancestors (a cycle) or another
  module. The error names both modules (`(top)` for the top level) and the
  folder.
- **BREAKING** (for broken workspaces only): a workspace that links a folder
  twice stops loading until one link is removed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: REQ-PROJ-006 "Workspace of modules" MODIFIED. Its description says
  a folder is at most one module, and it gets two new criteria (AC-PROJ-006.6
  a cycle, AC-PROJ-006.7 a folder linked twice).

## Impact

`src/specworks/core/workspace.py` (`_load_tree`) and `tests/test_modules.py`. No
API, data, config or dependency change.

## Out of Scope

- `module add` refusing, before writing, a folder that another parent already
  links. It writes the entry, the re-load then fails with this error, and
  `_insert_entry` rolls the edit back.
- The other suspected bugs.
