# Refinement: module-cycle-detection

## Problem

A module whose folder leads back to an ancestor through a symlink makes every
command crash. Reproduced: a project listing `loop: loop`, with `loop` a symlink
to `.`, fails with `RecursionError: maximum recursion depth exceeded`. A related
quiet case: one folder listed as a module by two parents (through a symlink or
two paths) is loaded twice under two names, so its changes appear twice and the
current module is picked arbitrarily. This was found as suspected bug 4 of
`baseline-project`.

## Context

**Observed:**
- `core/workspace.py`, `_load_tree`: recursively loads each listed module's
  config and its modules. It keeps no record of the folders already loaded.
- `core/validators.py`, `validate_relative`: module paths can't be absolute or
  contain `..`, so only a symlink can lead back up.
- `load_workspace` picks the current module as the first one whose root equals
  the nearest config folder (`next(...)`). With a folder loaded twice, that
  choice is arbitrary.
- `core/config_file.py`, `add_module_entry`: refuses a path already linked by
  the same parent, but not by another parent.
- Living spec of `project`: REQ-PROJ-006 (Workspace of modules) covers loading
  the tree, a missing module, and config names, but not cycles or repeats. The
  precedents are REQ-PROJ-005 (unique ID prefixes) and REQ-PROJ-016 (unique docs
  folders).

**Assumed:**
- No real workspace depends on one folder being two modules.

## Constraints

- [hard] No crash: a cycle is a clear error, not a `RecursionError`.
- [hard] A folder is at most one module of the workspace.
- [soft] The error names both module names (or the ancestor) and the folder,
  like the other uniqueness errors.

## Options

### Option A: Refuse a cycle

Fail when a module's resolved folder is one of its ancestors.

- **Pros:** Fixes the crash exactly.
- **Cons:** The "same folder, two parents" case stays silently wrong.
- **Effort:** S
- **Touches:** `project`

### Option B: Refuse any folder loaded twice

Fail when a module's resolved folder is already part of the workspace, either
as an ancestor (a cycle) or as another module, naming both.

- **Pros:** One rule covers the crash and the quiet duplicate. Consistent with
  REQ-PROJ-005 and REQ-PROJ-016.
- **Cons:** A workspace that lists a folder twice by accident stops loading
  until it is fixed, but that workspace is already inconsistent.
- **Effort:** S
- **Touches:** `project`

### Option C: Skip the repeat silently

Load each folder once and ignore later links to it.

- **Pros:** Nothing fails.
- **Cons:** Hides a wrong config, and which name the folder gets depends on the
  order of loading.
- **Effort:** S
- **Touches:** `project`

## Recommendation

**Option B**, chosen with the user. One rule, "a folder is at most one module",
fixes the crash and the duplicate case, and matches how the config treats other
ambiguities.

## Open Questions

None.

## Candidate Capabilities

- `project`: REQ-PROJ-006 MODIFIED, with new criteria for a module folder that
  is an ancestor (a cycle) and a folder linked as a module twice.
