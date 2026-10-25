# Tasks: move-config-into-spec-folder

## 1. The fixed layout

- [x] 1.1 Add the API as stubs: `WORKFLOW_DIR`, `CONFIG_FILE` and `find_old_config` in `src/specworks/core/config.py`; `load_config` without `dir` (REQ-PROJ-001, REQ-PROJ-021); verify `gate design` passes
- [x] 1.2 [test] Move the sample projects in `tests/helpers.py` and `tests/samples.py` to `.specworks/config.yml` + `.specworks/changes/`, and update the tests that name `spec.yml`, `spec/changes` or `<dir>` paths (REQ-PROJ-001, REQ-PROJ-020); delete the tests of the dropped AC-PROJ-001.3, AC-PROJ-006.3, AC-PROJ-009.2 and AC-CLI-003.4; verify the suite runs
- [x] 1.3 [test] Tests for AC-PROJ-001.1, .2, .4, .5, .6 (finding `.specworks/config.yml`) and AC-PROJ-020.1-.3, AC-PROJ-010.1-.4 on the new paths (REQ-PROJ-001, REQ-PROJ-010, REQ-PROJ-020); verify the new ones fail before 1.6
- [x] 1.4 [test] Tests for AC-PROJ-002.4 (the `dir` key message), AC-PROJ-006.1, .2, .4-.9 on the new layout, AC-PROJ-009.1 and .3 (REQ-PROJ-002, REQ-PROJ-006, REQ-PROJ-009); verify the changed ones fail before 1.6
- [x] 1.5 [test] Tests for AC-PROJ-021.1-.3 (old project, old module, both layouts) and AC-CLI-003.1, .3, .8 (init writes `.specworks/`, no `--dir`) (REQ-PROJ-021, REQ-CLI-003); verify they fail before 1.6 and 1.7
- [x] 1.6 [code] Find and load the config at `.specworks/config.yml`; `Config.dir` always `.specworks`; drop the several-configs error, the module file-name rule, `config_name` and `validate_dir`; the `dir` key error names `.specworks/` (REQ-PROJ-001, REQ-PROJ-002, REQ-PROJ-006, REQ-PROJ-009, REQ-PROJ-010, REQ-PROJ-020); verify the 1.3 and 1.4 tests pass
- [x] 1.7 [code] The old-layout error for a project and a module, the new layout winning over a leftover old file (REQ-PROJ-021); `init` without `--dir`, writing `.specworks/config.yml` from the template with comments for the fixed layout (REQ-CLI-003, REQ-PROJ-009); verify the 1.5 tests pass

## 2. This repo and the texts

- [x] 2.1 [code] Move this repo in the same commit as 1.6: `git mv spec.yml .specworks/config.yml` and `spec/changes` to `.specworks/changes`; update CLAUDE.md, the README, the skills (then `specworks skills`), templates and help texts that name `spec.yml` or `spec/` (REQ-PROJ-001); verify `specworks context` finds the project, `grep -rn "spec\.yml"` finds only archived changes, and `specworks run test` and `specworks run lint` pass
