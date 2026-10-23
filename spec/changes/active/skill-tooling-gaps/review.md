# Review: skill-tooling-gaps

Base: `origin/main`

## Findings

- [ ] R1 **test-gap** The suite fails: `test_build_gates_the_review_itself_when_every_finding_is_accepted` asserts ``runs `specworks gate review --change "<ref>" --allow-open` itself``, but the build skill (addressed to the coordinator as "you", like the rest of the file) says ``run `specworks gate review --change "<ref>" --allow-open` yourself``; the skill does what task 3.2 asks, the test pins the wording of task 3.1 instead of the skill's voice (`tests/test_skills.py:193`; `src/specworks/skills/specworks-build/SKILL.md:143`)
  - **Proposal**: back to test: assert ``run `specworks gate review --change "<ref>" --allow-open` yourself`` (the skill's wording), keeping the ``decided `accepted` `` check; the skill text stays as it is
- [ ] R2 **code-gap** The test skill fast-forwards the worktree only after `specworks start implement` (step 1, its third bullet), but that command runs `gate design` in the worktree; in a worktree that starts from an older commit (the case this change is about) design's stubs and phase are missing, so the gate fails first and the skill stops with "suggest `/specworks-design`" before it ever reaches the fast-forward (`src/specworks/skills/specworks-test/SKILL.md:42`, `:51`)
  - **Proposal**: back to code: move the worktree bullet to the top of step 1, before `specworks start implement` ("In a git worktree ..., first fast-forward it ...; then pick the change and start implement"), wording otherwise unchanged; refresh the installed copies with `specworks skills`

## Changed files without tags

None: `specworks review` lists no file under untracedSource or untracedTests. The changed skill files, their installed copies and `.gitignore` are not scanned for tags, and the change is `skip-specs` (no requirement or criterion to tag).

## Summary

The design, test and build skill edits and `.gitignore` cover the four gaps of the proposal; `.claude/worktrees/x` is ignored. Two findings stay open for the next cycle: R1 (test) the new wording check for the build skill expects "runs ... itself" where the skill says "run ... yourself", which fails the suite; R2 (code) the test skill's fast-forward comes after `specworks start implement`, whose `gate design` fails first in an outdated worktree. Nothing was changed in review.
