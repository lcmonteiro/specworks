# Proposal: code-half-no-tests

## Why

The code half runs the whole suite after each task, in its own checks and in
`gate code`, while this change's tests are written in parallel by the test
half and are missing or red by design. The tests only meet the code in
review, so the code half should check only that the code builds and is
clean.

## What Changes

- `specworks gate code` no longer runs `commands.test`. It runs `build`,
  `typecheck` and `lint`, each only when configured; a failing one blocks the
  gate. With none of the three configured, it passes with a warning that no
  build, typecheck or lint command is configured and the tests run in review.
- So `specworks gate implement` and `specworks start review` no longer run the
  suite; `gate review` and `validate` still do.
- The `specworks-code` skill no longer runs `specworks run test`: after a task
  it runs the task's own checks, and its project checks are build, typecheck
  and lint. The `specworks-build` skill says the suite meets the two halves in
  review.
- **BREAKING** (workflow): a broken existing test no longer stops `gate code`;
  it is first seen by `gate review`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `workflow`: REQ-FLOW-008 Gate code (its checks: build, typecheck and lint
  instead of the test command).

## Related requirements

Found with `specworks spec find "gate code" "code gate" "gate implement"
"commands.test" "commands.lint" lint typecheck "own tests"`:

- REQ-FLOW-008 modified.
- REQ-FLOW-014 left: `gate implement` still runs the test gate then the code
  gate; that it no longer runs the suite follows from REQ-FLOW-008.
- REQ-FLOW-006 left: the design gate keeps its build, typecheck and existing
  test checks.
- REQ-FLOW-013 left: validate keeps running test, lint and typecheck.
- REQ-SPECS-015 left: its warning still says the code half is verified by
  lint, typecheck or observable behaviour and the suite runs after the merge,
  which stays true (in review).
- REQ-PROJ-003, REQ-PROJ-007, REQ-PROJ-013, REQ-PROJ-025, REQ-CLI-013 left:
  they cover the config's command keys and running them, which do not change.

## Impact

- `src/specworks/workflow/gate.py` (`GATE_CHECKS["code"]`) and
  `src/specworks/workflow/checks.py` (`code_tests_pass` goes; `own_tests`
  stays for the design gate).
- `src/specworks/specs/check.py`: REQ-SPECS-015's suite warning says the suite
  runs in review instead of in `gate implement`.
- `src/specworks/skills/specworks-code/SKILL.md`,
  `src/specworks/skills/specworks-build/SKILL.md` and their installed copies.
- Tests of the code gate in `tests/test_code_phase.py` and the walkthrough.

## Out of Scope

- The design gate, the test half and `gate test`: unchanged.
- A config switch to run the tests in the code half again (refinement
  option B).
- Running lint in the design gate.
