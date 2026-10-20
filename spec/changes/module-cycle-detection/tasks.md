# Tasks: module-cycle-detection

## 1. A folder is at most one module

- [x] 1.1 Write failing tests in `tests/test_modules.py` for AC-PROJ-006.6 (`loop` symlink to the project) and AC-PROJ-006.7 (one folder linked as `billing` and, through a symlink, as `other`) tagged `@ac`; skip where symlinks can't be created; verify .6 fails with the `RecursionError` crash and .7 fails because the workspace loads
- [x] 1.2 In `_load_tree`, keep the resolved folder of every module loaded so far and fail with a `ConfigError` naming both modules and the folder when a module's folder is already taken (REQ-PROJ-006) tagged `@req REQ-PROJ-006`; verify the 1.1 tests and the existing AC-PROJ-006.x tests pass
