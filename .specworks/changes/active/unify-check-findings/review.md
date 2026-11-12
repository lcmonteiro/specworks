# Review: unify-check-findings

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **test-gap** AC-FLOW-019.1: the test asserts the Summary says 'Verdict: FAIL (2 critical, ', but REQ-FLOW-019 makes the verdict the one validate gives after writing, which also fails 'no open finding in validation.md' (V1, V2): 3 critical. The criterion only says the Summary says FAIL; the suite fails on it (tests/workflow/test_write_validation.py:78)
  - **Proposal**: back to test: assert the Summary's verdict line against the returned checks (summary(checks): 'Verdict: FAIL (3 critical, ...)', the two failed checks plus validation.md's open findings), not a hard-coded 2
  - **Decision**: back to test: check the Summary's verdict line against summary(checks) after the write (3 critical: the two failed checks plus validation.md's open V1 and V2) instead of a fixed 2
  - done in test: AC-FLOW-019.1 now checks the Summary's verdict line against summary(checks) after the write (3 critical: the two failed checks plus validation.md's open V1 and V2) instead of a fixed 2
  - confirmed in review: confirmed: tests/workflow/test_write_validation.py AC-FLOW-019.1 checks the Summary's verdict line against summary(checks) after the write (3 critical); the suite passes (1168 passed)
- [x] R2 **design-gap** design.md Decisions > 'Validate keeps its own findings in step with its checks', step 1 says write_validation leaves out only the validation artifact's own readability and open-findings checks; the code (src/specworks/workflow/validate.py:147, FINDINGS_CHECKS) also leaves out review.md's open-findings check, as REQ-FLOW-019 says ('other than the open findings of the check artifacts'). The code and spec agree; design.md is narrower, and close copies it into the living design
  - **Proposal**: back to design only: reword step 1 as 'every VALIDATE row except the open-findings checks of every check artifact and validation.md's readability check'
  - **Decision**: back to design only: change write_validation step 1 to read: every VALIDATE row except the open-findings checks of every check artifact and validation.md's readability check
  - done in design: design.md step 1 of write_validation now leaves out the open-findings checks of every check artifact and validation.md's readability check; step 5 reruns the ones left out
  - confirmed in review: confirmed: design.md step 1 of write_validation leaves out the open-findings checks of every check artifact and validation.md's readability check, matching FINDINGS_CHECKS in src/specworks/workflow/validate.py and REQ-FLOW-019; step 5 reruns them

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

- `tests/support/findings.py`: shared test helper (paths, check artifacts and writers for review.md and validation.md) used by the tagged tests of REQ-FLOW-010, 016, 018 and 019; no criterion of its own
- `tests/test_skills.py`: skill-wording test (validate now writes validation.md and commits); skills have no capability, so their tests stay untagged (CLAUDE.md)

## Summary

<!-- Two or three lines: what was found, what changed in code, specs and design, and anything sent back to an earlier phase. -->

The code matches the delta specs and design.md's Interfaces; every requirement has code and every criterion a test. Cycle 1 found two findings: R1 (test-gap, AC-FLOW-019.1 hard-coded 2 critical where the verdict after the write is 3) went back to test, and R2 (design-gap, design.md's step 1 of write_validation narrower than the spec and the code) went back to design only. Cycle 2 confirmed both carried out and closed them: the test now checks the verdict against summary(checks), design.md matches the code, and the suite passes. No code or spec changed in cycle 2; no new findings.
