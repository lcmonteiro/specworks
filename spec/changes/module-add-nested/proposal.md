# Proposal: module-add-nested

## Why

`module add` links a folder to the module it runs from, even when the folder
lies inside another module. The link then skips over that module, and the
workspace looks different depending on where a command runs (reproduced;
suspected bug 11 of `baseline-cli`; refinement.md, option A).

## What Changes

- `module add <path>` writes the link into the config of the innermost module
  that contains the folder, as `init <path>` already does, and prints the
  folder's full module name (`billing/sub`).
- Loading a workspace fails when a module's folder lies inside another module
  of the workspace that doesn't list it, naming the module it belongs under.
- `module add` refuses a folder that holds a module of the workspace, naming
  it, before writing anything; otherwise the new loading check would refuse
  the workspace it leaves behind (review R1).
- `module add` keeps refusing what it refuses today (a folder outside the
  current project, an existing config with another name, a duplicate).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`: REQ-CLI-005 "Registering modules and capabilities" MODIFIED. Its
  description says the link goes into the innermost module containing the
  folder, and it gets new criteria AC-CLI-005.6 and AC-CLI-005.7.
- `project`: REQ-PROJ-006 "Workspace of modules" MODIFIED. Its description says
  a module must be listed by the innermost module containing it, and it gets a
  new criterion, AC-PROJ-006.8.

## Impact

`src/specworks/cli/project.py` (`module_add`), `src/specworks/core/workspace.py`
(loading), and their tests. No API, data or dependency change. A hand-written
config that lists a module past the module containing it stops loading, with a
message saying where to move the link.

## Out of Scope

- Moving existing links automatically; the error says where it belongs.
- Changing `init <path>`, which already links to the nearest project above.
