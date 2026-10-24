# Review: fix-validate-test-task-skill

Base: `origin/main`

## Findings

- [ ] R1 **test-gap** The AC-FLOW-014.5 test still expects validate's removed `every task is done (specworks task list --pending)  -> /specworks-code` line, so it fails now that REQ-FLOW-013 (as modified) reports the open `[code]` task under `every [code] task is done (specworks task list --pending)  -> /specworks-code`; AC-FLOW-014.5 itself (start close names the phase of each failed check) still holds (`tests/test_validate_phase.py:148`)
  - **Proposal**: back to test: in `test_start_close_names_the_phase_that_fixes_each_failed_check`, expect `[FAIL] every [code] task is done (specworks task list --pending)  -> /specworks-code`; no code change. Recorded here as agreed with the user in design (design.md, "An existing AC-FLOW-014.5 test names the old task check").
  - **Decision**: waiting for the user

## Changed files without tags

None: `specworks review` lists no untraced source or test files.

## Summary

The code matches REQ-FLOW-013 and design.md: `unmarked_tasks_done` is as
agreed under `## Interfaces`, and `VALIDATE` replaces `tasks_done` with the
`[test]`, `[code]` and unmarked task checks (`/specworks-test`,
`/specworks-code`, `/specworks-design`); `tasks_done` is dropped. The
AC-FLOW-013.3 and AC-FLOW-013.8 tests check their THENs; lint and typecheck
pass. One finding: the AC-FLOW-014.5 test still names the old check (R1),
proposed back to the test half. No spec or design change.
