# Tasks: parallel-test-code

## 1. Phases and halves

- [x] 1.1 Add `implement` to `PHASES` (replacing test, code) and `HALVES` in `src/specworks/core/changes.py`, with stubs for reading a half as implement and refusing it in `set_phase` (REQ-PROJ-011); verify the suite still imports
- [x] 1.2 [test] Write failing tests for AC-PROJ-011.1, AC-PROJ-011.2, AC-PROJ-011.3, AC-PROJ-011.4, AC-PROJ-011.5 tagged `@ac`; verify they fail for the right reason
- [x] 1.3 [code] Implement the phase list, reading `test`/`code` as implement and refusing them (REQ-PROJ-011) tagged `@req`; verify `specworks run test` for the 1.2 tests

## 2. Task halves

- [x] 2.1 Add `Task.half` (and `half` in `to_dict`) as a stub in `src/specworks/specs/tasks.py` (REQ-SPECS-009); verify the suite still imports
- [x] 2.2 [test] Write failing tests for AC-SPECS-009.1, AC-SPECS-009.2, AC-SPECS-009.3, AC-SPECS-009.4, AC-SPECS-009.5, AC-SPECS-009.6, AC-SPECS-009.7 tagged `@ac`; verify they fail for the right reason
- [x] 2.3 [code] Read the `[test]`/`[code]` marker and warn in `check` when a half has no task (REQ-SPECS-009) tagged `@req`; verify the 2.2 tests

## 3. Status

- [x] 3.1 Add `half_progress(change)` as a stub in `src/specworks/workflow/artifacts.py` (REQ-FLOW-001); verify the suite still imports
- [x] 3.2 [test] Write failing tests for AC-FLOW-001.1, AC-FLOW-001.2, AC-FLOW-001.3, AC-FLOW-001.4 tagged `@ac`; verify they fail for the right reason
- [x] 3.3 [code] Compute each half's tasks for a change in implement and show them in `status` (REQ-FLOW-001) tagged `@req`; verify the 3.2 tests

## 4. Gates

- [x] 4.1 Add `tasks_done(half)` and the `implement` gate as stubs in `src/specworks/workflow/checks.py` and `src/specworks/workflow/gate.py` (REQ-FLOW-007, REQ-FLOW-008, REQ-FLOW-011, REQ-FLOW-014); verify the suite still imports
- [x] 4.2 [test] Write failing tests for AC-FLOW-007.1, AC-FLOW-007.2, AC-FLOW-007.3, AC-FLOW-007.4 tagged `@ac`; verify they fail for the right reason
- [x] 4.3 [test] Write failing tests for AC-FLOW-008.1, AC-FLOW-008.2, AC-FLOW-008.3, AC-FLOW-008.4, AC-FLOW-008.5, AC-FLOW-008.6, AC-FLOW-008.7 tagged `@ac`; verify they fail for the right reason
- [x] 4.4 [test] Write failing tests for AC-FLOW-011.1, AC-FLOW-011.2, AC-FLOW-011.3, AC-FLOW-011.4, AC-FLOW-011.5, AC-FLOW-011.6, AC-FLOW-011.7, AC-FLOW-011.8 tagged `@ac`; verify they fail for the right reason
- [x] 4.5 [test] Write failing tests for AC-FLOW-014.1, AC-FLOW-014.2, AC-FLOW-014.3, AC-FLOW-014.4, AC-FLOW-014.5, AC-FLOW-014.6, AC-FLOW-014.7, AC-FLOW-014.8 tagged `@ac`; verify they fail for the right reason
- [x] 4.6 [code] Scope the test and code gates to their half, drop `acs_have_tests` from the code gate, make its suite a warning with own `@ac` tests (REQ-FLOW-007, REQ-FLOW-008) tagged `@req`; verify the 4.2 and 4.3 tests
- [x] 4.7 [code] Make the review gate's suite a warning under `--allow-open` with an open finding (REQ-FLOW-011) tagged `@req`; verify the 4.4 tests
- [x] 4.8 [code] Add `gate implement`, expand implement to the test and code gates in `start`, refuse the halves (REQ-FLOW-014) tagged `@req`; verify the 4.5 tests

## 5. Review routing and cycles

- [x] 5.1 Replace `FINDING_PHASES` with `FINDING_STEPS` as a stub in `src/specworks/workflow/review.py` (REQ-FLOW-010, REQ-FLOW-012); verify the suite still imports
- [x] 5.2 [test] Write failing tests for AC-FLOW-010.1, AC-FLOW-010.2, AC-FLOW-010.3, AC-FLOW-010.4, AC-FLOW-010.5, AC-FLOW-010.6, AC-FLOW-010.7 tagged `@ac`; verify they fail for the right reason
- [x] 5.3 [test] Write failing tests for AC-FLOW-012.1, AC-FLOW-012.2, AC-FLOW-012.3, AC-FLOW-012.4, AC-FLOW-012.5, AC-FLOW-012.6 tagged `@ac`; verify they fail for the right reason
- [x] 5.4 [code] Route findings to steps, `back to implement:`, and done-in to the next step (REQ-FLOW-010) tagged `@req`; verify the 5.2 tests
- [x] 5.5 [code] Return the steps the open findings need from `next_cycle` (REQ-FLOW-012) tagged `@req`; verify the 5.3 tests

## 6. Help texts, instruction and skills

- [x] 6.1 [code] Update the CLI help (phase, start, gate) and the tasks instruction in `schema.yaml` to ask for `[test]`/`[code]` markers (REQ-FLOW-014, REQ-SPECS-009); verify `uv run specworks start --help` and `specworks instructions tasks`
- [x] 6.2 [code] Rework the build skill (implement's halves in parallel, the test half in a worktree, merging with every tick kept, the fallback), the test, code and review skills, the shared phase-subagents text, and every skill naming the phases `test`/`code` (REQ-FLOW-012, REQ-FLOW-014); verify `tests/test_skills.py` and the CLI-call check pass
- [x] 6.3 [code] Refresh the installed copies with `specworks skills`, then run `specworks run test` and `specworks run lint` (REQ-PROJ-011); verify both pass and coverage stays at 95% or more
