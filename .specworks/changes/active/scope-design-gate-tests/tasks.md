# Tasks: scope-design-gate-tests

## 1. The design gate

- [ ] 1.1 [test] In `tests/workflow/test_design_phase.py`, remove the three tests of the removed check (the existing-tests failure, the red suite with own tests, the changed test files) and the `TESTS` constant, and fix the tests that read `checks[TESTS]` (AC-FLOW-006.1, AC-FLOW-006.2, AC-FLOW-006.3, AC-FLOW-006.5, AC-FLOW-006.6); verify `uv run pytest tests/workflow/test_design_phase.py` has no test of the removed check
- [ ] 1.2 [test] Write a failing test for AC-FLOW-006.8 tagged `@ac AC-FLOW-006.8`: `commands.test` is a command that fails and leaves a marker file, `gate design` exits 0 with no check naming the tests and no marker file; verify it fails before the code change for the right reason (the check is present)
- [ ] 1.3 [test] Re-point the `--no-run` assertion tagged `@ac AC-FLOW-003.2` at the design gate's build and typecheck checks (AC-FLOW-003.2); verify `uv run pytest tests/workflow/test_design_phase.py`
- [ ] 1.4 [code] Remove `existing_tests_pass` from `src/specworks/workflow/gate.py` and from `GATE_CHECKS["design"]`, and `own_tests` and `has_own_ac_tests` from `src/specworks/workflow/checks.py`, tagged `@req REQ-FLOW-006` where a tag remains; verify `uv run ruff check src tests && uv run mypy` and that `specworks gate design` lists no test check

## 2. Skill text

- [ ] 2.1 [code] In `src/specworks/skills/specworks-design/SKILL.md` step 6, drop the test-run command and the paragraph about the existing suite (REQ-FLOW-006); verify by reading step 6: only build, typecheck, task ticks and the gate are left
- [ ] 2.2 [code] In `src/specworks/templates/tasks.md` line 5 say "verify it builds", and in `src/specworks/skills/specworks-baseline/SKILL.md` say validate (not the design and code gates) requires a green suite (REQ-FLOW-006); verify with a search for `existing tests pass` and `design and code gates` in `src/`
- [ ] 2.3 [test] In `tests/test_skills.py` change the baseline test's comment to say a red suite fails validate (REQ-FLOW-006); verify the comment no longer names the design and code gates
- [ ] 2.4 [code] Run `uv run specworks skills` to refresh `.claude/skills/` and commit them with the source (REQ-FLOW-006); verify `specworks context --json` reports skills `current`
