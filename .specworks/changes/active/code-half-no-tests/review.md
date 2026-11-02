# Review: code-half-no-tests

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **design-gap** design.md ## Interfaces calls no_code_commands 'a passing, non-blocking Check'; the code returns Check(ok=False, blocking=False) (src/specworks/workflow/checks.py:316), the [warn] form every other warning check uses, which matches AC-FLOW-008.4 'passes with the warning' (REQ-FLOW-008)
  - **Proposal**: back to design only: reword no_code_commands in ## Interfaces as 'a non-blocking warning Check (ok False, shown as [warn]; the gate still passes)'
- [ ] R2 **test-gap** AC-FLOW-008.4 test asserts the warning check has ok True and fails against the code (tests/test_code_phase.py:157)
  - **Proposal**: back to test: assert the check has ok False and blocking False (a [warn] line) with the pinned detail, and that the gate passes
- [ ] R3 **test-gap** the walkthrough asserts 'same code as the run at' in the output of start review, but start review runs gate test and gate code, which no longer run the suite and here run no command (tests/test_walkthrough.py:197; REQ-FLOW-008, proposal)
  - **Proposal**: back to test: drop that assertion on start review and assert the reuse on the following gate review, which runs the suite after sw run test
- [ ] R4 **code-gap** the review skill still says start review's test run is reused from the code gate; start review no longer runs the suite (src/specworks/skills/specworks-review/SKILL.md:51; REQ-FLOW-008)
  - **Proposal**: back to code: say neither gate runs the suite and it first meets the code in the next step (specworks run test), then run uv run specworks skills

## Changed files without tags

- `tests/test_walkthrough.py`: the end-to-end walkthrough, untagged by design; its change is covered by R3.

## Summary

The code matches REQ-FLOW-008 and the agreed API; the suite has 2 failures, both
tests at odds with the code (R2, R3), and design.md's wording of the warning
check disagrees with the [warn] convention the code follows (R1). The review
skill still describes the suite run that `start review` no longer does (R4).
Nothing fixed here: R1 back to design only, R2 and R3 back to test, R4 back to
code. The `check` warning that the MODIFIED REQ-FLOW-008 drops AC-FLOW-008.7
and AC-FLOW-008.8 is intended (proposal, task 1.4).
