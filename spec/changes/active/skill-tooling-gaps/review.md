# Review: skill-tooling-gaps

Base: `origin/main`

## Findings

- [x] R1 **test-gap** The suite fails: `test_build_gates_the_review_itself_when_every_finding_is_accepted` asserts ``runs `specworks gate review --change "<ref>" --allow-open` itself``, but the build skill (addressed to the coordinator as "you", like the rest of the file) says ``run `specworks gate review --change "<ref>" --allow-open` yourself``; the skill does what task 3.2 asks, the test pins the wording of task 3.1 instead of the skill's voice (`tests/test_skills.py:193`; `src/specworks/skills/specworks-build/SKILL.md:143`)
  - **Proposal**: back to test: assert ``run `specworks gate review --change "<ref>" --allow-open` yourself`` (the skill's wording), keeping the ``decided `accepted` `` check; the skill text stays as it is
  - **Decision**: back to test: assert ``run `specworks gate review --change "<ref>" --allow-open` yourself``, keeping the ``decided `accepted` `` check; the skill text stays as it is (agreed with the user)
  - Done in cycle 2 (test): `tests/test_skills.py:193` now asserts ``run `specworks gate review --change "<ref>" --allow-open` yourself``; the check passes, the skill text is unchanged
- [x] R2 **code-gap** The test skill fast-forwards the worktree only after `specworks start implement` (step 1, its third bullet), but that command runs `gate design` in the worktree; in a worktree that starts from an older commit (the case this change is about) design's stubs and phase are missing, so the gate fails first and the skill stops with "suggest `/specworks-design`" before it ever reaches the fast-forward (`src/specworks/skills/specworks-test/SKILL.md:42`, `:51`)
  - **Proposal**: back to code: move the worktree bullet to the top of step 1, before `specworks start implement` ("In a git worktree ..., first fast-forward it ...; then pick the change and start implement"), wording otherwise unchanged; refresh the installed copies with `specworks skills`
  - **Decision**: back to code: move the worktree bullet to the top of step 1 of the test skill, before `specworks start implement`, wording otherwise unchanged; refresh the installed copies (agreed with the user)
  - Done in cycle 2 (code): the worktree bullet is now the first bullet of step 1, before `specworks start implement`, in the skill and its three installed copies; its rewording of the next bullet is R3
- [ ] R3 **code-gap** The suite fails: R2's move reworded the next bullet of the test skill's step 1 from `Pick the change (above), then:` to `Then pick the change (above) and start implement:`; the existing shared-rule check `test_skills_pick_the_change_by_one_shared_rule[specworks-test]` asserts `Pick the change (above)` (capital P), which every other phase skill keeps (`src/specworks/skills/specworks-test/SKILL.md:47`; `tests/test_skills.py:271`)
  - **Proposal**: back to code: reword the bullet to `Pick the change (above) and start implement:` (dropping "Then"; the bullet order already puts it after the worktree step), refresh the installed copies with `specworks skills`; the shared-rule check stays as it is
  - **Decision**: back to code: reword the bullet to `Pick the change (above) and start implement:` and refresh the installed copies; the shared-rule check stays as it is (agreed with the user)

## Changed files without tags

None: `specworks review` lists no file under untracedSource or untracedTests. The changed skill files, their installed copies and `.gitignore` are not scanned for tags, and the change is `skip-specs` (no requirement or criterion to tag).

## Summary

Cycle 2: R1 and R2 were carried out and are closed. R2's move reworded the shared `Pick the change (above)` line of the test skill, which fails the existing shared-rule check: R3 (code) is open, decided with the user `back to code` (reword the bullet to `Pick the change (above) and start implement:` and refresh the installed copies); the next cycle runs code, then review. Lint and typecheck pass; the suite has one failure, R3 (`test_skills_pick_the_change_by_one_shared_rule[specworks-test]`).

Cycle 1:

The design, test and build skill edits and `.gitignore` cover the four gaps of the proposal; `.claude/worktrees/x` is ignored. Two findings stay open for the next cycle: R1 (test) the new wording check for the build skill expects "runs ... itself" where the skill says "run ... yourself", which fails the suite; R2 (code) the test skill's fast-forward comes after `specworks start implement`, whose `gate design` fails first in an outdated worktree. Both findings are decided with the user (`back to test` for R1, `back to code` for R2); the next cycle runs test | code, then review. Nothing was changed in review.
