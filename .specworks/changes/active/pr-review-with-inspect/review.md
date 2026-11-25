# Review: pr-review-with-inspect

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **code-gap** Inspect's end (step 7) has no path for a closed change whose second inspection only confirms notes: 'No notes: nothing is written' skips the commit and push of the ticks, while 'With notes' always says to request changes, although the PR review process (step 4 of 'Reviewing a pull request') says the reviewer approves when none is left open; the author's status would keep showing the notes waiting for the reviewer (src/specworks/skills/specworks-inspect/SKILL.md:185-219; reads REQ-CLI-025)
  - **Proposal**: back to code: in step 7, on a closed change, commit and offer the push whenever inspection.md changed (a note added or confirmed); then read status --json: with inspection.author, say to request changes (the pinned line); with no inspection left open, say to approve the pull request; with only inspection.reviewer, say which notes are still to confirm; refresh .claude/skills with uv run specworks skills

## Changed files without tags

- `tests/test_skills.py`: skill wording (inspect, reopen, onboard, refine); the skills have no capability yet, so these tests are untagged by the project's rule (CLAUDE.md, design.md "Pinned wording").

## Summary

The suite passes (1369 tests) and every requirement and criterion of REQ-FLOW-001, REQ-FLOW-020 and REQ-CLI-025..027 is implemented as specified, with tests that assert the pinned wording and JSON through the CLI; the code follows design.md's Interfaces and Decisions. One finding, in skill text: inspect's end has no path for a confirmation round on a closed change (R1, proposed back to code). Nothing changed in code, specs or design here. Candidate for a later change: an abandoned change with notes for the author is pointed to `/specworks-reopen`, which refuses abandoned changes (design.md decided not to special-case them).
