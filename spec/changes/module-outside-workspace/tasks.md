# Tasks: module-outside-workspace

## 1. Refuse a module outside the workspace

- [x] 1.1 Write failing tests in `tests/test_modules.py` for AC-PROJ-006.9 (a module symlinked outside, with and without a config there) tagged `@ac`, and remove `test_a_module_no_other_module_holds_passes_the_nesting_check`, which AC-PROJ-006.9 contradicts; verify the new tests fail because the workspace loads
- [ ] 1.2 In `_load_tree`, refuse a module whose resolved folder is outside the top level's, before reading its config, and drop `_check_nesting`'s `default=None` skip (REQ-PROJ-006) tagged `@req REQ-PROJ-006`; verify the 1.1 tests and the existing AC-PROJ-006.x tests pass
