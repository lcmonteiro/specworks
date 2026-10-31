# Tasks: deterministic-steps

## 1. The warning in check

- [x] 1.1 [test] Tests for AC-SPECS-015.1 (a `[code]` task naming a `[test]` task warns on its line, naming both; the `[test]` task does not), AC-SPECS-015.2 (a `[code]` task with `specworks run test` warns, naming it and the suite) and AC-SPECS-015.3 (no warning for another `[code]` task, a no-half task or a version number), asserting the pinned warning texts of design.md, tagged `@ac`; verify they fail before the code exists
- [x] 1.2 [code] Add the pass to `_check_tasks` in `src/specworks/specs/check.py` with the pinned warning texts (REQ-SPECS-015), tagged `@req`; verify `specworks run lint` passes and `specworks check --change deterministic-steps` warns on a sample `[code]` task that names a `[test]` task

## 2. The rules in the instructions and skills

- [x] 2.1 [test] Wording checks in `tests/test_skills.py` for the pinned phrases of design.md: the tasks and design instructions in `schema.yaml`, `specworks-code` and `specworks-test`, and `specworks-specify` step 7 fixing every `check` warning about the tasks; verify they fail before the text exists
- [x] 2.2 [code] Edit the tasks and design instructions in `src/specworks/schema.yaml` and the code, test and specify skills with the pinned phrases of design.md; refresh the installed copies with `uv run specworks skills`; verify `specworks run lint` passes and `specworks skills` reports the skills as current
