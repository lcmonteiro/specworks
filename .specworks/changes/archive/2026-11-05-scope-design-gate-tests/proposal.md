# Proposal: scope-design-gate-tests

## Why

The design gate runs the whole existing suite to check that the stubs break nothing, but build and typecheck already check the stubs and the review gate runs the tests against the change's code. The run is redundant, costs a full suite, and a red suite fails or warns the gate for reasons that are not about the API.

## What Changes

- **BREAKING**: `specworks gate design` no longer runs `commands.test`: the check `the existing tests still pass with the stubs (commands.test)` is gone, and a red suite never fails or warns the design gate.
- REQ-FLOW-006 loses its test rule and the "own tests" definition; AC-FLOW-006.4 and AC-FLOW-006.7 are removed.
- The gate's `own_tests` and `has_own_ac_tests` rules, used only by that check, are removed.
- The design skill (step 6), the `tasks.md` template and the baseline skill no longer say the design gate runs the tests; the design skill does not ask for a manual test run.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workflow`: REQ-FLOW-006 (Gate design) drops its test rule; AC-FLOW-006.4 and AC-FLOW-006.7 are removed, and a new criterion says the design gate runs no test command.

## Related requirements

- REQ-FLOW-006 modified: it states the existing-suite rule and the own-tests rule.
- REQ-FLOW-003 left: AC-FLOW-003.2 (`--no-run`) is about command checks in general; its test moves to the build and typecheck checks of the design gate.
- REQ-FLOW-008 left: the code gate already runs no tests.
- REQ-FLOW-011 left: the review gate keeps running the suite, including its warning under `--allow-open`.
- REQ-FLOW-017 left: the review gate's scoped tests are unchanged.
- REQ-FLOW-014 left: `gate implement` runs the test and code gates, not the design gate.
- REQ-PROJ-013, REQ-PROJ-028 left: running `test` and `test_scoped` is unchanged.
- REQ-SPECS-015 left: it is about task wording, not about which gate runs the suite.

## Impact

- Code: `src/specworks/workflow/gate.py` (the design check list), `src/specworks/workflow/checks.py` (`own_tests`, `has_own_ac_tests`).
- Docs: `workflow` living spec and design doc (written by close); skills `specworks-design`, `specworks-baseline` and the `tasks.md` template, then `specworks skills` to refresh the installed copies.
- Tests: `tests/workflow/test_design_phase.py` (the test-check tests are removed or moved).
- A broken existing test is first reported by the review gate instead of the design gate.

## Out of Scope

- The review, test and code gates, and `not_blocking` for the review gate's `--allow-open`.
- How `cycle` and `validate` run the tests (validate keeps the full suite).
- Running scoped tests at design.
