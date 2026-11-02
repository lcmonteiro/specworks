# Tasks: code-half-no-tests

## 1. The code gate runs build, typecheck and lint

- [ ] 1.1 Add `code_command(key, name)` and `no_code_commands(ctx)` as stubs in `src/specworks/workflow/checks.py` (REQ-FLOW-008); verify `uv run mypy` passes and the existing tests pass
- [ ] 1.2 [test] Rewrite the code gate tests in `tests/test_code_phase.py` for AC-FLOW-008.1, AC-FLOW-008.3 and AC-FLOW-008.4 (build, typecheck and lint commands instead of the test command; the warning when none is configured), tagged `@ac`; verify they fail on the stubs
- [ ] 1.3 [test] Write failing tests for AC-FLOW-008.9 (a failing or missing test command does not affect the gate) and AC-FLOW-008.10 (only typecheck configured: only it runs), tagged `@ac`; keep AC-FLOW-008.2, AC-FLOW-008.5 and AC-FLOW-008.6 passing with a passing build command; verify they fail on the stubs
- [ ] 1.4 [test] Delete the tests of the dropped AC-FLOW-008.7 and AC-FLOW-008.8 (REQ-FLOW-008), and update any other test that relied on `gate code` or `gate implement` running the test command; verify `specworks trace` shows no tag to them
- [ ] 1.5 [code] Implement `code_command` and `no_code_commands` with the pinned check names and warning, put them in `GATE_CHECKS["code"]` in place of `code_tests_pass`, and remove `code_tests_pass` (REQ-FLOW-008) tagged `@req REQ-FLOW-008`; verify `uv run ruff check src tests` and `uv run mypy` pass and `specworks gate code --change code-half-no-tests` shows mypy and ruff and no test command

## 2. Wording that pointed at the code half's suite

- [ ] 2.1 [code] Change the `check` warning for a `[code]` task that requires the suite in `src/specworks/specs/check.py` to the pinned wording (the suite runs in review after the merge) and the tasks instruction in `src/specworks/schema.yaml` to say the suite runs in review (REQ-FLOW-008); verify `specworks instructions tasks --change code-half-no-tests` shows it
- [ ] 2.2 [test] Update the pinned message of that warning in `tests/test_propose.py` to the new wording (REQ-FLOW-008); verify it fails until 2.1 is merged

## 3. Skills

- [ ] 3.1 [code] `src/specworks/skills/specworks-code/SKILL.md`: no test-command run after a task or in step 4 (build, typecheck and lint instead), and step 5 describes the gate as build, typecheck and lint with the tests meeting the code in review; `src/specworks/skills/specworks-build/SKILL.md`: the halves' tests meet the code in review, not in `gate implement`; then `uv run specworks skills` (REQ-FLOW-008); verify the installed copies match and the code skill no longer runs the test command
