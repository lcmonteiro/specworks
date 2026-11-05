# Design: scope-design-gate-tests

## Context

The design gate's check list in `src/specworks/workflow/gate.py` ends with `existing_tests_pass`, which runs `commands.test` and, for a red suite, asks `own_tests(ctx)` (in `checks.py`) whether the change has tests of its own to turn the failure into a warning. The code gate already runs no suite (`code-half-no-tests`), and the review gate runs the tests against the change (REQ-FLOW-011, REQ-FLOW-017). See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- The design gate runs no test command and shows no test check.
- No dead code stays behind: the rules only that check used are removed.

**Non-Goals:**
- Changing the review, test or code gates, or `not_blocking` (the review gate's `--allow-open` still uses it).

## Decisions

### Remove the check, do not scope it

The check and `own_tests` / `has_own_ac_tests` go; `GATE_CHECKS["design"]` keeps its other checks in order. Scoping the run to the touched capabilities (as `test_plan` does for review) was rejected: it keeps a test run and the "own tests" warning at design for what build and typecheck already cover. Serves: REQ-FLOW-006.

### Skill text follows the gate

The design skill's step 6 keeps `specworks run build`, `specworks run typecheck`, the task ticks and the gate, and drops `specworks run test` and the paragraph about the existing suite; it does not ask for a manual run. The `tasks.md` template's stub task says "verify it builds". The baseline skill says the suite must be green because validate requires it (a red suite cannot show that the baseline matches the code), no longer because the design and code gates do. The skills have no capability, so these edits are tasks without a requirement of their own, under REQ-FLOW-006.

**Pinned wording:** none; no test asserts these skill lines (the baseline test only checks the order of `specworks run test` and `specworks new`).

### The `--no-run` test moves

AC-FLOW-003.2 (`--no-run`) keeps its meaning; its design-gate test asserts it on the build and typecheck checks, since the test check no longer exists.

## Interfaces

None. The API only shrinks: `existing_tests_pass` (`src/specworks/workflow/gate.py`), `own_tests` and `has_own_ac_tests` (`src/specworks/workflow/checks.py`) are removed, and nothing outside the workflow capability uses them.

## Diagrams

No structural change.

## Risks / Trade-offs

- [A stub that breaks an existing test is caught at review, not design] -> the review gate runs the touched capabilities' tests and blocks on them; the same trade-off was accepted for the code gate.
- [Cached test results: a gate no longer warms the cache] -> later gates reuse a result only for the same code and run the command otherwise, so nothing breaks.

## Open Questions

None.
