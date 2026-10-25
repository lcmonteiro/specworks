# Tasks: skill-tooling-gaps

## 1. Design: the Proposed line

- [x] 1.1 [test] Add a wording check to `tests/test_skills.py`: the design skill names `Proposed: waiting for the user's agreement` and `Agreed with the user`; verify it fails before 1.2
- [x] 1.2 [code] In `specworks-design/SKILL.md`, write `## Interfaces` with `Proposed: waiting for the user's agreement` before stopping to agree on the API, and create the stubs only once it reads `Agreed with the user` (or the user agreed in the conversation); verify the 1.1 check passes

## 2. Test half: the worktree starts from the main checkout

- [x] 2.1 [test] Add a wording check: the test skill names `git worktree list` and `git merge --ff-only`, and the build skill no longer says "the worktree starts from HEAD"; verify it fails before 2.2
- [x] 2.2 [code] In `specworks-test/SKILL.md`, in a worktree, fast-forward to the main checkout's HEAD before writing tests (blocked if it is not a fast-forward); in `specworks-build/SKILL.md`, point to that check instead of assuming HEAD; verify the 2.1 check passes

## 3. Build: no empty review finish run

- [x] 3.1 [test] Add a wording check: the build skill says the coordinator runs `specworks gate review --change "<ref>" --allow-open` itself when every finding is decided `accepted`; verify it fails before 3.2
- [x] 3.2 [code] In `specworks-build/SKILL.md` step 3, skip the fresh review subagent when every finding is decided `accepted` and no finding from an earlier cycle needs ticking, and run the review gate directly; verify the 3.1 check passes

## 4. Tooling and installed copies

- [x] 4.1 [code] Add `.claude/worktrees/` to `.gitignore`; verify `git check-ignore .claude/worktrees/x` matches
- [x] 4.2 [code] Refresh the installed copies with `specworks skills`; verify `git diff` shows only the skill files, `.gitignore` and `tests/test_skills.py`
- [x] 4.3 [code] Run `specworks run test` and `specworks run lint`; verify both pass
