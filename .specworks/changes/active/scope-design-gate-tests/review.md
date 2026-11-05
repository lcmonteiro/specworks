# Review: scope-design-gate-tests

Base: `origin/main`

## Findings

- [ ] R1 **test-gap** tests/workflow/test_run_cache.py:25 (AC-FLOW-003.3): test_fresh_runs_each_command_once_for_all_the_gates_of_a_start fails (1 run, expects 2): it counts commands.test, which no gate of start review (design, test, code) runs any more; also tests/test_design_phase.py:1 docstring still says 'tests still pass'
  - **Proposal**: back to test: count the lint command (the code gate's) instead of the test command in that test, or expect 1 run, so it still checks that --fresh runs each command once for all the gates of a start; update the tests/test_design_phase.py docstring
- [ ] R2 **code-gap** src/specworks/skills/specworks-adopt/SKILL.md:100 and src/specworks/skills/specworks-start/SKILL.md:184 still say the design and code gates need commands.test to pass / wait for it (REQ-FLOW-006); neither gate runs the suite now, only review and validate do
  - **Proposal**: back to code: adopt says the review gate and validate need commands.test to pass; start says the first change's review gate waits for it; then run specworks skills and commit the installed copies
- [ ] R3 **design-gap** src/specworks/workflow/docs/design.md:108-121,141,265-266 (living design, written only by close): still describes the decision 'A change's own tests include its changed test files', own_tests and existing_tests_pass, and 'the design gate still runs the full suite'; the change's design.md does not record that these are overturned, so close would keep them (REQ-FLOW-006)
  - **Proposal**: back to design only: add a Decision to the change's design.md saying the 'own tests' decision, own_tests/has_own_ac_tests/existing_tests_pass and the design gate's full-suite run are overturned, so close drops them from the living design.md; do not edit the living doc by hand

## Changed files without tags

- `tests/test_skills.py`: a comment-only edit in the baseline skill test (the red suite now fails validate); no behaviour, no tag needed.

## Summary

The code, spec and design.md agree: REQ-FLOW-006 and AC-FLOW-006.8 are implemented and tested, and the removed rules leave no dead code. Three open findings (a stale test run-count test, stale skill text, the living design.md the close step must drop) are proposed for the next cycle; the full suite has one failing test (R1).
