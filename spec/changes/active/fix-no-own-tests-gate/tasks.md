# Tasks: fix-no-own-tests-gate

## 1. The change's own tests

- [x] 1.1 Add `own_tests(ctx)` as a stub in `src/specworks/workflow/checks.py` (REQ-FLOW-006, REQ-FLOW-008); verify the suite still passes
- [x] 1.2 [test] Write failing tests for AC-FLOW-006.4, AC-FLOW-006.7 (the design gate with changed test files, without them, and without git) tagged `@ac`; verify they fail for the right reason
- [x] 1.3 [test] Write failing tests for AC-FLOW-008.3, AC-FLOW-008.7, AC-FLOW-008.8 (the code gate with `@ac` tests, with changed test files in a skip-specs change, and with neither) tagged `@ac`; verify they fail for the right reason
- [x] 1.4 [code] Implement `own_tests` from `@ac` tests or changed test files in `ctx.report` (REQ-FLOW-006, REQ-FLOW-008) tagged `@req`; verify the suite and lint pass
- [x] 1.5 [code] Use `own_tests` in `existing_tests_pass` and `code_tests_pass`, the warning naming the reason (REQ-FLOW-006, REQ-FLOW-008) tagged `@req`; verify `specworks run test` and `specworks run lint` pass
