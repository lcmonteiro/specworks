# Review: fix-validate-test-task-skill

Base: `origin/main`

## Findings

- [x] R1 **test-gap** The AC-FLOW-014.5 test still expects validate's removed `every task is done (specworks task list --pending)  -> /specworks-code` line, so it fails now that REQ-FLOW-013 (as modified) reports the open `[code]` task under `every [code] task is done (specworks task list --pending)  -> /specworks-code`; AC-FLOW-014.5 itself (start close names the phase of each failed check) still holds (`tests/test_validate_phase.py:148`)
  - **Proposal**: back to test: in `test_start_close_names_the_phase_that_fixes_each_failed_check`, expect `[FAIL] every [code] task is done (specworks task list --pending)  -> /specworks-code`; no code change. Recorded here as agreed with the user in design (design.md, "An existing AC-FLOW-014.5 test names the old task check").
  - **Decision**: back to test: expect `[FAIL] every [code] task is done (specworks task list --pending)  -> /specworks-code` in the AC-FLOW-014.5 test; no code change (agreed with the user)
  - done in test: `test_start_close_names_the_phase_that_fixes_each_failed_check` now expects `[FAIL] every [code] task is done (specworks task list --pending)  -> /specworks-code` (commit f9e0a9c); confirmed in review cycle 2: the full suite passes (609 tests)

## Changed files without tags

None: `specworks review` lists no untraced source or test files.

## Summary

The code matches REQ-FLOW-013 and design.md: `unmarked_tasks_done` is as
agreed under `## Interfaces`, and `VALIDATE` replaces `tasks_done` with the
`[test]`, `[code]` and unmarked task checks (`/specworks-test`,
`/specworks-code`, `/specworks-design`); `tasks_done` is dropped. The
AC-FLOW-013.3 and AC-FLOW-013.8 tests check their THENs; lint and typecheck
pass. One finding: the AC-FLOW-014.5 test still named the old check (R1),
sent back to the test half and done in cycle 2; the suite passes. No spec or
design change.
