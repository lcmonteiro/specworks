# Design: module-add-nested

## Context

`module_add` (`src/specworks/cli/project.py`) links the folder to `ws.current`,
while `link_to_parent` (used by `init <path>`) links to the nearest project
above the folder. `load_workspace` (`src/specworks/core/workspace.py`) loads the
tree from the top level down and already refuses a folder that is two modules
(`_load_tree`), but not a module listed past the module that contains it. The
change touches two capabilities (`cli`, `project`); see proposal.md.

## Goals / Non-Goals

**Goals:**
- `module add` and `init <path>` pick the same owner for a folder.
- Every workspace that loads has one shape, whatever folder it is loaded from.

**Non-Goals:**
- Rewriting a wrong config; the error says where the link goes.

## Decisions

### `module add` links to `ws.owner(folder)`

`Workspace.owner(path)` already returns the innermost module whose folder holds
a path. `module_add` keeps its refusal of a folder outside `ws.current`, then
writes the link into `ws.owner(root)`'s config with the path relative to that
module, and prints the full name from the re-loaded workspace. Recomputing the
owner from the parent folder's configs (as `link_to_parent` does) was rejected:
the workspace is already loaded and knows every module. Serves: REQ-CLI-005.

### Loading checks each module against its innermost container

After the tree is loaded, a new `_check_nesting(ws)` (next to
`_check_prefixes` and `_check_docs_folders`) checks, for each module but the
top, that the innermost other module whose folder contains its folder is its
parent. Otherwise it raises a `ConfigError`:
`module 'sub' (services/billing/sub) is inside module 'billing'; list it in billing's config instead`.
Folders are compared resolved, as `_load_tree` does. Missing modules are not
loaded, so they are not checked. Checking inside `_load_tree` was rejected: a
later sibling can be the container, so the check needs the whole tree.
Serves: REQ-PROJ-006.

## Interfaces

None: `module add`'s arguments and JSON output keep their shape; the new check
is private to `src/specworks/core/workspace.py`.

## Risks / Trade-offs

- [A workspace with a link past its container stops loading] -> the error names
  the module and where its link belongs; nobody can rely on today's shape, which
  already differs depending on where a command runs.
