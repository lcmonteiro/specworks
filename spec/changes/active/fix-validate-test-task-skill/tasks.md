# Tasks: fix-validate-test-task-skill

## 1. Open tasks by kind

- [x] 1.1 Add the API as a stub: a check in `src/specworks/workflow/checks.py` for open tasks with no `[test]` or `[code]` marker (REQ-FLOW-013); verify `gate design` passes
- [x] 1.2 [test] Update the AC-FLOW-013.3 test in `tests/test_validate_phase.py` to expect `every [code] task is done (specworks task list --pending)` naming `/specworks-code` (AC-FLOW-013.3); verify it fails against today's single task check
- [x] 1.3 [test] Add a test tagged `@ac AC-FLOW-013.8`: with an open `[test]` task, `[code]` task and unmarked task, each kind's check fails listing only its own tasks and naming `/specworks-test`, `/specworks-code` and `/specworks-design`, and `goBackTo` lists all three (AC-FLOW-013.8); verify it fails before 1.4
- [x] 1.4 [code] Replace `tasks_done` in validate's `VALIDATE` table with the `[test]` check (`/specworks-test`), the `[code]` check (`/specworks-code`) and the unmarked check (`/specworks-design`), tagged `@req REQ-FLOW-013`; drop `tasks_done` if nothing else uses it (REQ-FLOW-013); verify the 1.2 and 1.3 tests pass and `specworks run test` and `specworks run lint` pass
