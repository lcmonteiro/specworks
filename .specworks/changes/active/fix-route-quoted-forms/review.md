# Review: fix-route-quoted-forms

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **test-gap** the suite fails: test_back_to_on_the_finding_line_counts (tests/test_build_cycle.py:139, tagged AC-FLOW-010.3) still expects a 'back to design:' on the finding's own line to route it to design; MODIFIED REQ-FLOW-010 makes the finding's own line text, so the code (src/specworks/workflow/review.py parse_review) rightly routes it to code by its type
  - **Proposal**: back to test: rewrite that test to the new rule, keeping its tag: the same finding line is routed to code by its type, not design (rename it e.g. test_back_to_on_the_finding_line_is_text); no code change
  - **Decision**: back to test: rewrite test_back_to_on_the_finding_line_counts (tests/test_build_cycle.py) to assert the finding is routed to code by its type, keep its @ac AC-FLOW-010.3 tag, and rename it test_back_to_on_the_finding_line_is_text

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

None: every changed source and test file carries its tags.

## Summary

<!-- Two or three lines: what was found, what changed in code, specs and design, and anything sent back to an earlier phase. -->

The code follows REQ-FLOW-010 and REQ-FLOW-016 and the design's line-start rule; re-reading the 58 archived
reviews with it changes only R2 and R3 of `skip-halves-for-design-text`, as the proposal says. One finding: an
older test (R1, test-gap) still asserts the old rule and fails the suite; proposed back to the test half. No
spec, design or code change.
