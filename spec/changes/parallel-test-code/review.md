# Review: parallel-test-code

Base: `origin/main`

The suite passes (546 tests), lint and typecheck pass, branch coverage is 98%.
Every requirement has `@req` code and every criterion an `@ac` test; the code
exposes the interfaces under `## Interfaces` in design.md (plus internal
helpers: `half_error`, `has_own_ac_tests`, `not_blocking`,
`run_implement_gate`, `NEXT_STEP`), and the tests assert each THEN through the
CLI or the public functions.

## Findings

- [ ] R1 **quality** Text still describes `test` and `code` as phases and the old cycle rule: README.md says `/specworks-build` runs "design → test → code → review" and starts a new cycle "at the earliest phase the findings need" (`README.md:69`, `README.md:93-96`); the comment block above `TYPE_PHASE` still speaks of `back to <phase>` and "the phase that resolves each finding type" (`src/specworks/workflow/review.py:200-209`) (REQ-FLOW-010, REQ-FLOW-012)
  - **Proposal**: back to code: README.md says "design → implement (test | code) → review" and that a new cycle runs only the steps the findings need (code half, test half, both halves, or design then both); the review.py comments say step (specify, design, implement, test, code) instead of phase
  - **Decision**: back to code: README.md says "design → implement (test | code) → review" and that a new cycle runs only the steps the findings need (code half, test half, both halves, or design then both); the review.py comments say step (specify, design, implement, test, code) instead of phase
  - done in code: README.md's flow line, phase table, step 4 and `/specworks-build` paragraph now say design → implement (test | code) → review and that a new cycle runs only the steps the findings need; the comment block above `TYPE_PHASE` in review.py says step instead of phase
- [x] R2 **spec-gap** The code gate's failing suite is only a warning whenever the change has `@ac` tests "of its own", and for a MODIFIED requirement those include the tests that existed before the change (`has_own_ac_tests` in `src/specworks/workflow/checks.py:261`, used by `code_tests_pass`). So for a change that only modifies requirements (like this one), the code gate never blocks on the suite, even before the test half wrote anything, and a regression in unrelated tests is only a warning there; the refinement meant the code half to run the existing suite as its regression check (REQ-FLOW-008, AC-FLOW-008.3, AC-FLOW-008.7)
  - **Proposal**: accept as it is: those pre-existing tests encode the old behaviour of the MODIFIED criteria and are expected to fail until the test half updates them, the gate cannot tell them apart from unrelated tests without running them one by one, the code skill still requires the existing tests to stay green, and the review gate runs the whole suite and blocks on it. (Alternative: back to specify: count only tests of ADDED criteria, or test files changed on the branch, as "its own".)
  - **Decision**: accepted: the pre-existing tests of MODIFIED criteria are expected to fail until the test half updates them and the gate cannot tell them from unrelated tests; the code skill still keeps existing tests green and the review gate blocks on the whole suite

## Changed files without tags

- `tests/samples.py`: sample project data; its tasks gain the `[test]` / `[code]` markers that the gates of REQ-FLOW-007 and REQ-FLOW-008 now read
- `tests/test_walkthrough.py`: the end-to-end walkthrough, updated to `start implement` and the task markers (REQ-PROJ-011, REQ-FLOW-014); it carries no single criterion

## Summary

Code, specs and design agree; the tests meet the code with no failure. Two
findings, decided with the user: R1 (stale README and review.py comments)
stays open, back to code, for the next cycle (code half, then review); R2
(the code gate's suite is only a warning for a change with MODIFIED
requirements) is accepted. No spec or design/API change. Out of scope, a
candidate for a new change: validate's "every task is done" names
`/specworks-code` even when the open task is a `[test]` task.
