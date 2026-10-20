# Proposal: unique-capability-paths

## Why

Two capabilities registered on the same code path share one living-docs folder.
One then reads the other's requirements as its own, and close can merge both
into one spec.md (suspected bug 1 of `baseline-project`; refinement.md, option
A).

## What Changes

- Loading a workspace fails when two capabilities, in any modules, resolve to
  the same docs folder (`<module root>/<path>/<docs_dir>`). The error names both
  capabilities and the folder, and asks to give one its own path.
- `capability add` is refused the same way, leaving the config unchanged.
- Nested paths (`src/auth` and `src/auth/admin`) stay allowed.
- **BREAKING** (for broken configs only): a config that already shares a path
  stops loading until one capability is moved.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: ADDED REQ-PROJ-016 (unique docs folders), next to REQ-PROJ-005
  (unique ID prefixes).

## Impact

- `src/specworks/core/workspace.py`: the check at load, next to
  `_check_prefixes`.
- `src/specworks/cli/project.py` (`capability add`): a check before writing,
  next to the one for ID prefixes. The re-load in `_insert_entry` would already
  roll a shared path back, but it replaces the loader's error with a generic
  "add it by hand", which wouldn't name the capability that owns the path.
- New tests.

No new dependency or config key.

## Out of Scope

- Two capabilities sharing a folder on purpose (one docs file per capability):
  option C, not asked for.
- A capability path that lies inside another capability's docs folder.
- The other suspected bugs from the baselines.
