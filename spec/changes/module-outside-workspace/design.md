# Design: module-outside-workspace

## Decisions

### Checked where each module's folder is resolved

`_load_tree` already resolves each child's folder for the cycle check. Right
after that check, and before `load_module_config`, it refuses a folder that is
not inside the top level's (the first folder in `seen`), raising a
`ConfigError`: `module 'ext' (ext) leads outside the workspace, to <folder>; a
module's folder must be inside the top level's`. So a missing module that points
outside is refused too, and nothing outside is read. With every module inside
the top level, the top level holds every module, so `_check_nesting` always
finds a container: its `default=None` skip goes. Serves: REQ-PROJ-006.

## Interfaces

None: `load_workspace` keeps its signature and still raises `ConfigError`.
