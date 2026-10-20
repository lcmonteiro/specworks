# Tasks: module-add-nested

## 1. Loading refuses a module listed past its container

- [ ] 1.1 Write a failing test in `tests/test_modules.py` for AC-PROJ-006.8 (a top level listing `billing: services/billing` and `sub: services/billing/sub`) tagged `@ac`; verify it fails because the workspace loads
- [ ] 1.2 Add `_check_nesting(ws)` to `load_workspace`, raising a `ConfigError` that names the module and the module it belongs under (REQ-PROJ-006) tagged `@req REQ-PROJ-006`; verify the 1.1 test and the existing AC-PROJ-006.x tests pass

## 2. `module add` links to the module containing the folder

- [ ] 2.1 Write a failing test in `tests/test_modules.py` for AC-CLI-005.6 (`module add services/billing/sub` from the top level) tagged `@ac`; verify it fails because the link lands in the top level's config
- [ ] 2.2 In `module_add`, write the link into `ws.owner(root)`'s config with the path relative to it, and print the full module name (REQ-CLI-005) tagged `@req REQ-CLI-005`; verify the 2.1 test and the existing AC-CLI-005.x tests pass
