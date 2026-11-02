# Tasks: capability-tests

## 1. A capability's test folder and the config keys

- [x] 1.1 Add the config stubs in design.md's Interfaces to `src/specworks/core/config.py`: `COMMAND_KEYS` with `test_scoped`, `SCOPED_TEST_KEY`, `PATHS_PLACEHOLDER`, `DEFAULT_TESTS_DIR`, `Capability.tests` and `Capability.tests_path` (returning `root / self.path` for now), `Config.tests_dir`, and `tests_dir`/`tests` in `CONFIG_KEYS`/`CAPABILITY_KEYS` (REQ-PROJ-003, REQ-PROJ-004, REQ-PROJ-027); verify `specworks run lint` passes and the existing tests pass
- [ ] 1.2 [test] Write failing tests for AC-PROJ-027.1 to AC-PROJ-027.4 in `tests/test_capability_tests.py` (default `tests/<name>`, the module's `tests_dir`, a capability's `tests`, inside a module), and extend the tests of AC-PROJ-003.1 (`tests_dir` and a capability's `tests` that leave the project) and add AC-PROJ-003.8 (a `test_scoped` without `{paths}`), tagged `@ac`; verify they fail for the right reason
- [ ] 1.3 [code] Load and validate `tests_dir` and a capability's `tests` with `validate_relative`, implement `Capability.tests_path`, and refuse a `test_scoped` without `{paths}` naming `commands.test_scoped` (REQ-PROJ-027, REQ-PROJ-003, REQ-PROJ-004), tagged `@req`; verify `specworks run lint` passes and `specworks context` loads this repo's config

## 2. Setting and running the scoped command

- [x] 2.1 Add the runner stubs in design.md's Interfaces to `src/specworks/core/runner.py`: `scoped_command` (returning the unfilled command), `run_scoped`, and the keyword-only `command` on `run_command` and `cached_run` (REQ-PROJ-028, REQ-PROJ-013); verify `specworks run lint` passes and the existing tests pass
- [ ] 2.2 [test] Write failing tests for AC-PROJ-028.1 to AC-PROJ-028.3 (the folders filled in and quoted, a space in a folder name; relative to a module's folder; reuse only for the same folders), AC-PROJ-013.5 (`specworks run test_scoped` refused, nothing runs), the key list in AC-PROJ-013.4, and AC-PROJ-025.13 (`config set commands.test_scoped`, refused without `{paths}` and the file unchanged), tagged `@ac`; verify they fail for the right reason
- [ ] 2.3 [code] Add `test_scoped` to `COMMAND_KEYS` (after `test`; the stub left it out), implement `scoped_command` and `run_scoped` as design.md decides, the `command` argument of `run_command`/`cached_run` with the refusal of a bare `test_scoped`, and the `{paths}` refusal in `set_config_value` (REQ-PROJ-028, REQ-PROJ-013, REQ-PROJ-025), tagged `@req`; verify `specworks run lint` passes and running the `test_scoped` key through `specworks run` on this repo prints the refusal

## 3. The review gate runs the touched capabilities' tests

- [x] 3.1 Add the stubs in design.md's Interfaces to `src/specworks/workflow/checks.py`: `TestPlan`, `test_plan` (returning a full-suite plan), `GateContext.test_plan`, `test_folders_exist` (returning `None`), and list `test_folders_exist` in the review gate in `src/specworks/workflow/gate.py` (REQ-FLOW-017); verify `specworks run lint` passes and the existing tests pass
- [ ] 3.2 [test] Write failing tests for AC-FLOW-017.1 to AC-FLOW-017.8 in `tests/test_capability_tests.py` on sample projects whose test commands record what they ran (only the touched folder; a changed source or test file touching its capability; no `test_scoped`; a missing folder warned with the full suite; nothing touched; a failing scoped run blocking, a warning under `--allow-open` with an open finding; another module's capability run in its module; validate running everything), tagged `@ac`; verify they fail for the right reason
- [ ] 3.3 [code] Implement `test_plan`, `test_folders_exist` and the scoped runs in `review_tests_pass` as design.md decides (REQ-FLOW-017, REQ-FLOW-011), tagged `@req`; verify `specworks run lint` passes and `specworks gate review --change capability-tests --no-run --json` lists the test folder check

## 4. `context` and the default config

- [ ] 4.1 [test] Extend the test of AC-CLI-004.1: each capability in `context --json` has `testsPath` relative to the workspace root, also when the folder does not exist, tagged `@ac AC-CLI-004.1`; verify it fails for the right reason
- [ ] 4.2 [code] Add `testsPath` to `context`'s capability entries in `src/specworks/cli/project.py`, and commented `tests_dir` and `commands.test_scoped` examples to the default config text in `src/specworks/core/config_file.py` (REQ-CLI-004, REQ-PROJ-027), tagged `@req`; verify `specworks context --json` on this repo shows `testsPath: tests/project` and `specworks run lint` passes
