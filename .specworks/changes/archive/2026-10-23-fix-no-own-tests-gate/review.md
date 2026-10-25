# Review: fix-no-own-tests-gate

Base: `origin/main`

## Findings

None.

## Changed files without tags

- `tests/helpers.py`: test helper (`on_a_branch`) for the tests of AC-FLOW-006.7, AC-FLOW-008.3 and AC-FLOW-008.8; it holds no test of its own, so it needs no `@ac` tag

## Summary

The code, the delta specs and design.md agree. `own_tests(ctx)` in
`src/specworks/workflow/checks.py` returns the reason (`@ac` tests, or changed
test files from `ctx.report.changed`, deleted ones excluded, `None` without git),
and both `existing_tests_pass` and `code_tests_pass` use it, computing it only
for a red suite as the design's risk note says. Each criterion's test asserts
its THEN, including the warning text and the cases without git and with no
changed test file. The suite (605 tests) and lint pass. Nothing was changed in
review and nothing is sent back.
