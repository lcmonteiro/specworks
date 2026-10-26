# Tasks: merge-halves-without-conflicts

## 1. Merging a half's branch

- [x] 1.1 Add the API as stubs: `merge_branch`, `MergeResult`, `BranchMergeError` and `merge_ticks` in `src/specworks/workflow/merge.py`, and the `merge` command in `src/specworks/cli/workflow.py` (REQ-FLOW-015, REQ-CLI-010); verify `gate design` passes
- [ ] 1.2 [test] Tests for AC-FLOW-015.1-.6 with real git repositories and a second branch: no conflict, ticks on both sides, the trace on both sides, another file conflicting, a task's text differing, uncommitted changes and an unknown branch; each aborted case checks the files and HEAD are as before (REQ-FLOW-015); verify they fail against the stubs
- [ ] 1.3 [test] Tests for AC-CLI-010.1-.3: the `--json` output with workspace-relative paths, an aborted merge's error and exit 1, and a project outside git (REQ-CLI-010); verify they fail against the stubs
- [x] 1.4 [code] Implement `merge_ticks` and `merge_branch`: refuse a dirty checkout or unknown branch, merge, abort on any conflict but the change's `tasks.md` and `traceability.md`, merge the ticks, regenerate the trace, commit (REQ-FLOW-015); verify the 1.2 tests pass
- [x] 1.5 [code] The `merge` command with its text and `--json` output and errors as values (REQ-CLI-010); verify the 1.3 tests pass

## 2. The build skill

- [x] 2.1 [code] In `specworks-build/SKILL.md` step 2, merge the worktree's branch with `specworks merge <branch> --change "<ref>"` and stop on its error, replacing the manual tick and trace resolution; refresh the installed copies with `specworks skills` (REQ-FLOW-015); verify `tests/test_skills.py` passes and `specworks run test` and `specworks run lint` pass
