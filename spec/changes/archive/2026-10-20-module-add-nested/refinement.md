# Refinement: module-add-nested

## Problem

`specworks module add` links a folder to the module it runs from, even when the
folder lies inside another module. Reproduced: from the top level, with
`billing` at `services/billing`, `module add services/billing/sub` writes
`sub: services/billing/sub` into the top level's config and prints
`linked . as module '(top)'`. Seen from the top, `sub` is a module of the top
level. Seen from inside `sub`, it is a workspace of its own, because `billing`
doesn't list it. This was found as suspected bug 11 of `baseline-cli`. It is not
covered by `module-cycle-detection`: the folder is loaded once, just under the
wrong parent.

## Context

**Observed:**
- `cli/project.py`, `module_add`: links the folder to `ws.current`, the module
  holding the working directory, and prints `ws.current` of the workspace
  re-loaded from the new folder.
- `cli/project.py`, `link_to_parent` (used by `init <path>`): links the folder
  to the nearest project above it, so `init` and `module add` disagree.
- `core/workspace.py`, `load_workspace`: rises from the nearest config only
  through ancestors that list it (REQ-PROJ-006). A module listed by an ancestor
  higher than its nearest one breaks that chain.
- Living specs: `cli` REQ-CLI-005 (registering modules) and `project`
  REQ-PROJ-006 (workspace of modules).

**Assumed:**
- Nobody relies on a module listed past the module that contains it, since its
  workspace already differs depending on where a command runs.

## Constraints

- [hard] A folder's module is listed by the innermost module that contains it,
  so the workspace is the same from every folder.
- [hard] `module add` keeps refusing what it refuses today (a folder outside
  the project, an existing config with another name, a duplicate).
- [soft] `module add` and `init <path>` link the same way.

## Options

### Option A: Link to the module that contains the folder

`module add <path>` writes the link into the config of the innermost module
containing the folder, from wherever it runs, and prints that folder's full
module name. Loading refuses a module whose folder is inside another module
that doesn't list it, naming the module it belongs under.

- **Pros:** `module add` and `init` agree, the workspace looks the same from
  everywhere, and a hand-written mistake is caught too.
- **Cons:** The link lands in a config the user didn't run from, but the output
  says which one.
- **Effort:** S
- **Touches:** `cli`, `project`

### Option B: Refuse instead

`module add` fails when the folder is inside another module, saying to run it
from there. Loading refuses as in A.

- **Pros:** Nothing is written anywhere unexpected.
- **Cons:** An extra step, and `init` and `module add` still differ.
- **Effort:** S
- **Touches:** `cli`, `project`

### Option C: Fix only the message

- **Pros:** Smallest change.
- **Cons:** The two views of the workspace stay inconsistent.
- **Effort:** S
- **Touches:** `cli`

## Recommendation

**Option A**, chosen with the user. `module add` then behaves like `init`, every
folder has one place in the tree, and the loading check catches the same
mistake in a hand-edited config.

## Open Questions

None.

## Candidate Capabilities

- `cli`: REQ-CLI-005 MODIFIED. `module add` links to the module containing the
  folder.
- `project`: REQ-PROJ-006 MODIFIED. Loading refuses a module listed past the
  module containing it.
