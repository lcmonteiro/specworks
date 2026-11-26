# Review: pr-review-with-inspect

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **code-gap** Inspect's end (step 7) has no path for a closed change whose second inspection only confirms notes: 'No notes: nothing is written' skips the commit and push of the ticks, while 'With notes' always says to request changes, although the PR review process (step 4 of 'Reviewing a pull request') says the reviewer approves when none is left open; the author's status would keep showing the notes waiting for the reviewer (src/specworks/skills/specworks-inspect/SKILL.md:185-219; reads REQ-CLI-025)
  - **Proposal**: back to code: in step 7, on a closed change, commit and offer the push whenever inspection.md changed (a note added or confirmed); then read status --json: with inspection.author, say to request changes (the pinned line); with no inspection left open, say to approve the pull request; with only inspection.reviewer, say which notes are still to confirm; refresh .claude/skills with uv run specworks skills
  - **Decision**: back to code: on a closed change, commit and offer the push whenever inspection.md changed (a note added or confirmed), then read status --json: author notes -> request changes on the pull request; nothing open -> approve the pull request; only reviewer notes -> name the notes still to confirm; run uv run specworks skills
  - done in code: inspect step 7: on a closed change, commits and offers the push whenever inspection.md changed (note added or confirmed), then reads status --json: author notes -> request changes (pinned line); nothing open -> approve the pull request; only reviewer notes -> names the notes still to confirm; installed copy refreshed
  - confirmed in review: inspect step 7 now commits and offers the push whenever inspection.md changed (note added or confirmed) and reads status --json: author notes -> request changes (pinned line), nothing open -> approve, only reviewer notes -> names them; .claude/skills copy refreshed
- [x] R2 **code-gap** R1's fix reworded inspect step 7's '**No notes: nothing is written.**' to '**inspection.md unchanged (no note added or confirmed): nothing is written.**', dropping wording pinned by the earlier change add-inspect-skill; tests/test_skills.py:923 test_the_inspect_skill_carries_its_pinned_wording[No notes: nothing is written] now fails (1 failed, 1368 passed) (src/specworks/skills/specworks-inspect/SKILL.md:186)
  - **Proposal**: back to code: keep the pinned phrase and add the new condition after it, e.g. '**No notes: nothing is written.** When no note was added or confirmed, inspection.md is unchanged; the human review is its own record ...'; leave the test as it is; run uv run specworks skills to refresh .claude/skills
  - **Decision**: back to code: put the pinned phrase 'No notes: nothing is written.' back in step 7 of src/specworks/skills/specworks-inspect/SKILL.md, with the new condition (only when inspection.md did not change) after it; leave tests/test_skills.py as it is; run uv run specworks skills
  - done in code: inspect step 7: the pinned '**No notes: nothing is written.**' is back, followed by the condition that it holds only while inspection.md is unchanged; test_skills.py untouched; installed copy refreshed
  - confirmed in review: confirmed in review: inspect step 7 carries the pinned '**No notes: nothing is written.**' again, with the condition (inspection.md unchanged) after it; tests/test_skills.py untouched; .claude/skills in sync (uv run specworks skills: no diff); suite 1369 passed

## Changed files without tags

- `tests/test_skills.py`: skill wording (inspect, reopen, onboard, refine); the skills have no capability yet, so these tests are untagged by the project's rule (CLAUDE.md, design.md "Pinned wording").

## Summary

Cycle 3. R1 (cycle 2) and R2 are confirmed: inspect's step 7 ends a confirmation round on a closed change (commit and push whenever inspection.md changed, then request changes, approve, or name the notes still to confirm, from `status --json`), and carries the pinned '**No notes: nothing is written.**' again, so the suite passes (1369 passed). No new finding: the only change since the last review is that sentence in the inspect skill and its installed copy, which are in sync. Every requirement and criterion of REQ-FLOW-001, REQ-FLOW-020 and REQ-CLI-025..027 still has its code and tests; nothing changed in code, specs or design here. Candidate for a later change: an abandoned change with notes for the author is pointed to `/specworks-reopen`, which refuses abandoned changes (design.md decided not to special-case them).
