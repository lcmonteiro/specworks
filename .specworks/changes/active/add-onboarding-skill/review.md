# Review: add-onboarding-skill

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **design-gap** The Decision "State from `specworks context --json`" picks the next skill for a change in flight from its phase alone, so a `baseline-<capability>` change (from `/specworks-adopt`) in design, implement or review is sent to `/specworks-build <ref>`; a baseline only adds tags and runs its own design, implement and review in `/specworks-baseline`, which then hands it to `/specworks-done baseline-<capability>`, so a brownfield user is pointed to the wrong skill (design.md "State from `specworks context --json`"; `src/specworks/skills/specworks-onboard/SKILL.md:58`)
  - **Proposal**: back to design: in that Decision, add the baseline case to the changes in flight: `baseline-<capability>` in specify, design, implement, or review before `gate review` passes: `/specworks-baseline <capability>`; in review once `gate review` passes, validate or close: `/specworks-done baseline-<capability>`; then the code half adds the same line to the skill (`/specworks-baseline` and `/specworks-done` are already pinned, so the test half has nothing new unless design pins more wording)
  - **Decision**: back to design: add a baseline case to the Decision "State from specworks context --json": a baseline-<capability> change goes to /specworks-baseline <capability> in specify, design or implement, or in review before gate review passes; once gate review passes, and in validate or close, to /specworks-done baseline-<capability>; then the code half writes the same in the skill
  - done in design: design.md Decision 'State from specworks context --json' gains the baseline case: /specworks-baseline <capability> in specify, design, implement or review before gate review passes; /specworks-done baseline-<capability> after; the code half writes it in the skill
  - done in implement: code half: src/specworks/skills/specworks-onboard/SKILL.md step 1 adds the baseline case (/specworks-baseline <capability> before gate review passes, /specworks-done baseline-<capability> after); installed copy refreshed
  - confirmed in review: confirmed: design.md's Decision and SKILL.md step 1 (lines 61-67) send a baseline-<capability> change to /specworks-baseline <capability> before gate review passes and to /specworks-done baseline-<capability> after, matching specworks-baseline's hand-over; installed copy is current
- [x] R2 **quality** specworks-adopt's description triggers on a bare "onboard", so a user saying "onboard" may get adopt instead of the new specworks-onboard
  - **Proposal**: back to code: drop "onboard" from the quoted triggers in src/specworks/skills/specworks-adopt/SKILL.md's description, keep "onboard a codebase", and refresh the installed copies
  - **Decision**: back to code: drop "onboard" from the quoted triggers in specworks-adopt's description (keep "onboard a codebase") and refresh the installed copies with specworks skills
  - done in code: dropped the bare "onboard" trigger from specworks-adopt's description (kept "onboard a codebase"); installed copies refreshed with specworks skills
  - confirmed in review: confirmed: specworks-adopt's description no longer quotes a bare "onboard" (keeps "onboard a codebase"); .claude/skills copy matches and specworks context reports the skills current

## Changed files without tags

None: `specworks review` lists no untracedSource or untracedTests (the change is `skip-specs`; the skill, README and installed copy are not scanned, and `tests/test_skills.py` carries existing `@ac` tags).

## Summary

Cycle 1: two findings, both sent back: R1 (design-gap), the per-phase next step sent a baseline change to `/specworks-build` (back to design, then the code half); R2 (quality), specworks-adopt's description also triggered on a bare "onboard" (back to code).

Cycle 2: both carried out and closed. The skill's step 1 now has the baseline case agreed in design.md, and specworks-adopt's description no longer quotes "onboard"; the installed copies are current. The suite passes (874 tests), and every read command the skill names exists in the CLI. No new findings; no spec, API or code changed in review.
