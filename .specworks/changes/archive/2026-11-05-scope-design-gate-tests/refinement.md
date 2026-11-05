# Refinement: scope-design-gate-tests

## Problem

The design gate runs the whole existing test suite (`commands.test`) to check that the stubs break nothing. At design the change has no tests of its own (they come with the implement phase), so the run is redundant: build and typecheck already check the stubs, and the tests first meet the change's code in the review gate. It also costs a full-suite run, and a red suite makes the gate fail or warn for reasons that are not about the API. The code gate already dropped its suite run for the same reason (`code-half-no-tests`).

## Outcomes

- `specworks gate design` runs no test command and lists no test check; it still checks the Interfaces section, the files it names, build and typecheck.
- A red suite never fails or warns the design gate, so no "own tests" warning appears there.
- A stub that breaks an existing test is first caught by the review gate, as already happens for the code half.
- The design skill, the `tasks.md` template and the baseline skill no longer say the design gate runs the tests.

## Context

**Observed:**
- `src/specworks/workflow/gate.py`: `existing_tests_pass` (REQ-FLOW-006) runs `commands.test`; a red suite is only a warning when `own_tests(ctx)` finds `@ac` tests or changed test files.
- `src/specworks/workflow/checks.py`: `own_tests` and `has_own_ac_tests` are used only by that check; `not_blocking` is also used by `review_tests_pass`.
- `src/specworks/workflow/docs/spec.md`: REQ-FLOW-006, scenarios AC-FLOW-006.4 and AC-FLOW-006.7 cover the test check; `docs/design.md` records it under "A change's own tests include its changed test files" (`fix-no-own-tests-gate`) and in the `own_tests` interface list.
- `tests/workflow/test_design_phase.py` tags AC-FLOW-006.4 (two tests), AC-FLOW-006.7 and AC-FLOW-003.2 against the test check.
- Text saying the design gate runs the suite: `skills/specworks-design/SKILL.md` step 6, `templates/tasks.md` line 5, `skills/specworks-baseline/SKILL.md` ("the design and code gates require it", stale for the code gate).
- The code gate does not run tests (`code-half-no-tests` in the workflow design doc); the review gate runs the touched capabilities' tests (REQ-FLOW-017).

**Assumed:**
- No other code reads `own_tests` or the design test check's name (the grep found none in `src/`).
- Dropping the design run does not remove a cached result that later gates rely on (they reuse results only when the code is the same, and run otherwise).

## Constraints

- [hard] The review gate keeps running the tests, so existing behaviour stays protected before close.
- [hard] Never renumber or reuse an ID: AC-FLOW-006.4 and AC-FLOW-006.7 are removed, not reused.
- [hard] Living docs are written by `specworks close`, not by hand; skill text is edited in `src/specworks/skills/` and the installed copies refreshed with `specworks skills`.
- [soft] Keep the design gate's other checks unchanged.

## Options

### Option A: Drop the design gate's test check

Remove `existing_tests_pass` from `GATE_CHECKS["design"]`, and with it `own_tests` and `has_own_ac_tests`. Rewrite REQ-FLOW-006 without the test rule, remove AC-FLOW-006.4 and AC-FLOW-006.7, and update the design skill, the `tasks.md` template and the baseline skill. The design skill does not ask for a manual test run.

- **Pros:** the gate and the skill agree; one place (review) where tests meet the change; less code and fewer scenarios.
- **Cons:** a stub that breaks an existing test is caught later, at review (the same trade-off accepted for the code gate).
- **Effort:** S
- **Touches:** `workflow` (gate, checks, spec, design doc), skills (`specworks-design`, `specworks-baseline`), `templates/tasks.md`
- **Outcomes:** meets all four.

### Option B: Run only the touched capabilities' tests at design

Reuse `test_plan` (REQ-FLOW-017) so the design gate runs `test_scoped` for the capabilities with a delta spec.

- **Pros:** faster than the full suite; the same plan as review.
- **Cons:** still a test run and a test check at design, redundant with build and typecheck; keeps the "own tests" rule or needs a new one.
- **Effort:** M
- **Touches:** `workflow`
- **Outcomes:** fails the first two (a test check remains and can still fail or warn).

### Option C: Keep the full suite (do nothing)

- **Pros:** no work; stubs are checked against every existing test early.
- **Cons:** the redundancy and cost remain.
- **Effort:** S
- **Touches:** none
- **Outcomes:** fails all four.

## Recommendation

Option A (agreed with the user): the design gate checks the API and that the stubs build; the tests run in review.

## Open Questions

- None.

## Candidate Capabilities

- `workflow`: modified - REQ-FLOW-006 loses its test rule (AC-FLOW-006.4 and AC-FLOW-006.7 removed, AC-FLOW-003.2 reviewed if it names the design test check).
