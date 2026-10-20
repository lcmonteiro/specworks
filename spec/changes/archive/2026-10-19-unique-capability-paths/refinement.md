# Refinement: unique-capability-paths

## Problem

Two capabilities can be registered with the same code path. Their living docs
then share one `<path>/<docs_dir>/` folder. In a scratch project with `auth` and
`login` both on `src/auth`, `spec show login` lists `REQ-AUTH-001` as its own,
and closing a change to `login` would merge `REQ-LOGIN-…` into auth's spec.md,
mixing two capabilities in one file. This was found as suspected bug 1 of
`baseline-project`.

## Context

**Observed:**
- `core/config.py` (`load_config`) validates each capability's path on its own
  (relative, inside the project) but never compares paths.
- `core/workspace.py` (`_check_prefixes`) refuses to load a workspace in which
  two capabilities share an ID prefix, naming both. It runs on every load, so
  `capability add` (`core/config_file.py`, `_insert_entry`) also re-loads after
  writing and rolls the edit back when loading fails.
- A capability's living spec is `<module root>/<path>/<docs_dir>/spec.md`
  (`Capability.docs_path`, `specs/capabilities.py` `living_spec`), and
  `specs/merge.py` writes there at close. Paths are relative to each module's
  folder, so capabilities of different modules can reach the same folder.
- Nested paths (`src/auth` and `src/auth/admin`) get different docs folders and
  work today.
- Living spec of `project`: REQ-PROJ-004 (capabilities in the config) and
  REQ-PROJ-005 (unique ID prefixes, the precedent).

**Assumed:**
- No real project uses a shared path on purpose: today it gives wrong results.

## Constraints

- [hard] A workspace in which two capabilities share a docs folder must not
  load. Close must never write one capability's spec into another's file.
- [hard] Nested capability paths stay allowed.
- [hard] `capability add` must leave the config unchanged when it is refused.
- [soft] The check and its message follow the ID-prefix check: same place, both
  capabilities named, a fix suggested.

## Options

### Option A: Refuse at load, like duplicate prefixes

When the workspace loads, compare each capability's resolved docs folder across
all modules, and fail naming both capabilities and the shared folder, asking to
give one its own path. `capability add` is refused through its existing re-load
and rollback.

- **Pros:** The bad state can't exist. Consistent with REQ-PROJ-005. Catches
  overlapping modules. Small.
- **Cons:** A config that already has a shared path stops loading until it is
  edited, but that config is already broken.
- **Effort:** S
- **Touches:** `project`

### Option B: Refuse in `capability add`, warn at load

- **Pros:** Existing configs keep loading.
- **Cons:** The state can still be written by hand, and close can still mix two
  specs.
- **Effort:** S
- **Touches:** `project`, `cli`

### Option C: Allow it, with a docs file per capability

A shared folder holds `docs/<name>/spec.md` per capability.

- **Pros:** Supports two capabilities in one folder on purpose.
- **Cons:** Changes the docs layout, which needs migration and a design. Nobody
  has asked for it.
- **Effort:** M
- **Touches:** `project`, `specs`

## Recommendation

**Option A**, chosen with the user. A shared docs folder is always wrong today,
so refusing it is the same kind of rule as the one for duplicate ID prefixes.
The check compares resolved docs folders, so it covers capabilities in different
modules and leaves nested paths allowed. Refusing in `capability add` comes free
from the re-load it already does.

## Open Questions

None that block the proposal.

## Candidate Capabilities

- `project`: modified. A new requirement next to REQ-PROJ-005 (unique docs
  folders), and REQ-PROJ-008's refusals now include a shared path.
