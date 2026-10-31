# Review: deterministic-steps

Base: `origin/main`

## Findings

- [x] R1 **design-gap** REQ-SPECS-015 says "Each warning SHALL say that the code half is verified by lint, typecheck or observable behaviour and that the suite runs after the merge", but the pinned warning for a named `[test]` task (design.md Pinned wording), which the code writes verbatim, says "the code half cannot see the test half's tests until the merge; verify it with lint, typecheck or observable behaviour": it never says the suite runs after the merge. The suite warning does. AC-SPECS-015.1's THEN asks only for the line and both task numbers, so the tests pass either way (`src/specworks/specs/check.py:402`; `design.md:38`; `specs/specs/spec.md:9`)
  - **Proposal**: accepted: the warning says the same in its own words (the test half's tests are only seen after the merge), and its exact text was agreed with the user as pinned wording in design. Alternative: back to design: extend the pinned phrase to `...until the merge, where the suite runs in gate implement; verify it with lint, typecheck or observable behaviour`, then the test and code halves follow it
  - **Decision**: accepted: the warning says the same in its own words, and its exact text was agreed as pinned wording in design (agreed with the user)

- [x] R2 **quality** In `specworks-code` step 3.6 the new "Existing tests must stay green (step 4 fixes what fails)" points to "step 4" inside a numbered list whose item 4 is "Tag the code"; it means the top-level step 4, "Run the project's checks". An agent following the skill can read it as the tagging step (`src/specworks/skills/specworks-code/SKILL.md:93`, and its installed copy)
  - **Proposal**: back to code: write "(step 4, Run the project's checks, fixes what fails)" in `src/specworks/skills/specworks-code/SKILL.md` and refresh the installed copy with `uv run specworks skills`; no pinned phrase or wording test changes
  - **Decision**: back to code: write "(step 4, Run the project's checks, fixes what fails)" in `specworks-code` step 3.6 and refresh the installed copy (agreed with the user)
  - done in code: `specworks-code` step 3.6 now reads "Existing tests must stay green (step 4, Run the project's checks, fixes what fails)" in `src/specworks/skills/specworks-code/SKILL.md` and its installed copy (`uv run specworks skills` reports them current); checked in review, cycle 2

- [x] R3 **design-gap** The Decision "Existing sample tasks that break the new rule" opens with "Resolved without a new task: the test half reworded both samples in its own commit (task 1.1)", then keeps the superseded paragraph "The proposal: a new `[test]` task 1.3 rewords both ... (e.g. `verify lint passes and the reset link is sent` ...)". There is no task 1.3, and the samples now read `verify lint passes`. Close folds this Decision into the living `design.md`, so the paragraph would record a plan that never happened (`design.md:48`, `design.md:62`)
  - **Proposal**: back to design: replace the superseded proposal paragraph with what was done: the test half reworded `tests/samples.py` task 1.2 and `tests/test_walkthrough.py` task 1.3 to `verify lint passes`, kept every assertion, and updated the one detail string in `tests/test_validate_phase.py` that quotes the sample. No API, test or code change follows
  - **Decision**: back to design: replace the superseded proposal paragraph of the Decision "Existing sample tasks that break the new rule" with what was done (agreed with the user)
  - done in design: the paragraph proposing a new `[test]` task 1.3 is replaced by what the test half did (samples.py task 1.2 and test_walkthrough.py task 1.3 reworded to `verify lint passes`, assertions kept, the test_validate_phase.py detail string updated); no API, test or code change follows
  - checked in review, cycle 2: the Decision now describes only what was done, and matches the diff of `tests/samples.py`, `tests/test_walkthrough.py` and `tests/test_validate_phase.py`

## Changed files without tags

- `tests/samples.py`: shared sample data, not a test of a criterion. Its `[code]` task 1.2 no longer names task 1.1, so the new REQ-SPECS-015 warning does not fire in the tests that expect no `check` warnings (design.md Decision "Existing sample tasks that break the new rule"; R3 covers how that Decision is worded)
- `tests/test_walkthrough.py`: the walkthrough's sample `tasks.md` text, reworded for the same reason (task 1.3 no longer names task 1.2); its assertions are unchanged

## Summary

The `_check_tasks` pass (REQ-SPECS-015) does what the three criteria say: it matches only the change's own `[test]` numbers, as whole tokens, plus the literal `specworks run test`, and the tests assert the pinned texts, lines and the controls. The schema instructions and the code, test and specify skills carry the pinned phrases, and their installed copies match. Cycle 1 found three findings: R1 accepted (the first warning says the same in its own pinned words), R2 sent back to code and R3 back to design. Cycle 2 carried both out: the code skill's "step 4" now names "Run the project's checks", and the design Decision on the sample tasks records what was done. No new findings. The suite (699 tests) passes.
