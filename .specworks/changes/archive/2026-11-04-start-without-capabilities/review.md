# Review: start-without-capabilities

Base: `6fcb845` (the commit before this change's refine; `origin/main` is behind the stacked `tighten-telemetry-tests` work)

## Findings

- [x] R1 **test-gap** tests/test_skills.py:750 still requires `<!-- specworks:include architecture -->` in specworks-start; the code half rightly dropped it (it asks for a block diagram and `specworks diagrams --dir`, against design.md Decision "The first architecture has no capabilities yet"), so the suite fails (src/specworks/skills/specworks-start/SKILL.md:153)
  - **Proposal**: back to test: remove specworks-start from the parametrize of test_the_skills_that_write_the_architecture_include_its_shared_text (keep close and adopt) and assert start does not include the shared architecture text, so start asks for no block diagram
  - **Decision**: back to test: remove specworks-start from the parametrize of test_the_skills_that_write_the_architecture_include_its_shared_text (keep close and adopt) and assert start does not include the shared architecture text
  - done in test: dropped specworks-start from test_the_skills_that_write_the_architecture_include_its_shared_text and added test_start_does_not_include_the_shared_architecture_text
  - confirmed in review: test_the_skills_that_write_the_architecture_include_its_shared_text now covers close and adopt only, and test_start_does_not_include_the_shared_architecture_text asserts start has no architecture include; the suite passes (998)

## Changed files without tags

- `tests/test_skills.py`: skill-wording tests; the change is `skip-specs` and the skills have no capability, so there is no `@ac` to tag (design.md, Pinned wording). Its failing test was finding R1, fixed in cycle 2.

## Summary

The skill, template, instruction and README text match design.md's Pinned wording, and onboard's new rows and the refusal in start's step 1 agree on what a fresh config is. One drift: the code half dropped start's `<!-- specworks:include architecture -->` (which asks for a block diagram and `specworks diagrams --dir`, against the Decision "The first architecture has no capabilities yet"), but the existing test that requires that include for `specworks-start` was not updated, so the suite failed (R1, back to test). Cycle 2: the test half dropped start from that test and added `test_start_does_not_include_the_shared_architecture_text`; R1 is closed and the suite passes (998). No new findings. Nothing changed in specs or design.
