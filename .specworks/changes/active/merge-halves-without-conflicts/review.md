# Review: merge-halves-without-conflicts

Base: `origin/main`

## Findings

- [ ] R1 **test-gap** AC-FLOW-015.5 fails, and AC-FLOW-015.2 / AC-CLI-010.1 do not really put a tick on the branch side only (`tests/test_merge.py:42`, `:139`, `:89`, `:118`, `:201`)
  - What happens: in `commit_on(halves, "main", {TASKS_MD: tick(halves, "1.2")}, ...)`, `tick()` reads `tasks.md` from the working tree before `commit_on` checks out `main`, so it reads the branch's version. The main side's `tasks.md` then already carries the branch's edits: in AC-FLOW-015.5 the text change is on both sides, `merge_ticks` sees no difference, and the merge succeeds (`DID NOT RAISE BranchMergeError`); in AC-FLOW-015.2, `test_both_files_conflicting_are_both_resolved` and AC-CLI-010.1 the main side has both ticks, so the tests would still pass if the merge kept only the main side's ticks.
  - The code is right: the same scenarios with each side built from the baseline `tasks.md` (checked in a scratch test during review) abort on the differing text with the checkout as before, and keep the tick that only the branch made. `merge_ticks` alone is covered by its unit tests.
  - **Proposal**: back to test: build each side's `tasks.md` from the baseline (e.g. `tick()` reads the committed baseline with `git show <baseline>:<path>`, or the main side is computed after checking out `main`), so in AC-FLOW-015.2, AC-FLOW-015.5, AC-CLI-010.1 and the both-files test the branch-only tick (and the text change) are on the branch side only; no code change.
  - **Decision**: back to test: build each side's tasks.md from the baseline, so the branch-only tick and the text change are on the branch side only; no change to code, spec or design (agreed with the user)

## Changed files without tags

None: `specworks review` lists no untracedSource or untracedTests. The skill
copies (`src/specworks/skills/specworks-build/SKILL.md`, `.claude/skills/`,
`.github/skills/`, `.github/prompts/`) are Markdown and are not scanned for
tags; their change is task 2.1 (REQ-FLOW-015).

## Summary

The code matches REQ-FLOW-015, REQ-CLI-010 and design.md's interfaces and
merge flow; every requirement has tagged code and every criterion a test.
One test-gap (R1): the tests build the main side's `tasks.md` from the
branch's checkout, so AC-FLOW-015.5 fails and the tick-merging tests assert
too little. Proposed back to test; no spec, design or code change.
