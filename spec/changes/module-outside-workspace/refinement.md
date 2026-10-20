# Refinement: module-outside-workspace

## Problem

A module whose folder, after following symlinks, is outside the workspace
breaks the workspace. Reproduced: a top level listing `ext: ext`, with `ext` a
symlink to a folder elsewhere, makes `context` and `module list` crash with a
`ValueError` from `Workspace.rel`. From inside `ext`, the working directory
resolves to the outside folder, so `ext` loads as a top level of its own. Found
while fixing `module-add-nested` (its review R2); the crash is on `origin/main`
too.

## Context

**Observed:**
- `core/workspace.py`: `_load_tree` resolves each module's folder (`seen`, the
  cycle check of `module-cycle-detection`); `Workspace.rel` resolves a path and
  takes it relative to the root, raising for a folder outside it;
  `_check_nesting` skips a module no other module holds (review R2 of
  `module-add-nested`), the only case of which is a module outside the
  workspace.
- `core/config.py`, `find_root`: resolves the working directory before walking
  up.
- Living spec: `project` REQ-PROJ-006 (workspace of modules).

**Assumed:**
- Nobody uses such a workspace today, since `context` crashes on it.

## Constraints

- [hard] Every module's folder is inside the top level's, so every path the CLI
  prints is relative to the root and the workspace looks the same from every
  folder.
- [hard] Loading fails with an error, never a crash.
- [soft] A symlink whose target stays inside the workspace keeps working (the
  cycle and duplicate checks already handle it).

## Options

### Option A: Refuse at load

Loading fails naming the module, its path, and where its folder really is,
before reading its config (so a missing outside module is refused too).

- **Pros:** Small, the same place and pattern as the cycle check; the R2 skip
  becomes dead code and goes.
- **Cons:** A layout that symlinks a checkout from elsewhere is not supported;
  it must be moved or copied inside.
- **Effort:** S
- **Touches:** `project`

### Option B: Support outside modules

- **Pros:** Symlinked checkouts work.
- **Cons:** Every resolved path (`rel`, module roots, `find_root`, the cycle
  check) would need rethinking; large and risky.
- **Effort:** L
- **Touches:** `project`, `cli`

### Option C: Only stop the crash

- **Pros:** Smallest.
- **Cons:** The workspace still differs from inside `ext`.
- **Effort:** S
- **Touches:** `project`

## Recommendation

**Option A**, chosen with the user.

## Open Questions

None.

## Candidate Capabilities

- `project`: REQ-PROJ-006 MODIFIED. A module whose folder is outside the top
  level's fails loading.
