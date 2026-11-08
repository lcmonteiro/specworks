# Tasks: harness-chat-only

## 1. The command opens an empty chat

- [x] 1.1 Reshape the stubs per design.md Interfaces: `harness()` with no parameter, `run_harness(ws)`, `build_harness(ws, model, *, frontend=None)`, `GitBackend(ws, module)` and `signature(folder)`; remove `first_peer`, `HarnessSession` and `GitBackend.load` (REQ-CLI-022, REQ-HARNESS-009); verify `uv run ruff check src tests && uv run mypy` and `uv run specworks harness --help`
- [ ] 1.2 [test] Update the tests of `specworks harness` with no argument, tagged `@ac AC-CLI-022.1`, `@ac AC-CLI-022.2`, `@ac AC-CLI-022.5`; add tests for the empty chat and the refused `--change`, tagged `@ac AC-CLI-022.6`, `@ac AC-CLI-022.7`; delete the tests of the retired AC-CLI-022.3 and AC-CLI-022.4; verify the new ones fail on the stubs
- [ ] 1.3 [test] Update the test of AC-HARNESS-009.2 to start from the user's first message, delete the test of the retired AC-HARNESS-009.3, and add a test for an existing change continued, tagged `@ac AC-HARNESS-009.2`, `@ac AC-HARNESS-009.5`; keep AC-HARNESS-009.1 and 009.4 passing; replace every `request=` or `change=` given to `build_harness` in other harness tests by a user message; verify the new ones fail on the stubs
- [ ] 1.4 [code] Implement the command, `run_harness` and `build_harness` without a request or change (REQ-CLI-022) tagged `@req REQ-CLI-022`; verify `uv run specworks harness --change x` exits with a usage error
- [ ] 1.5 [code] Implement the backend's change finding by folder signature and remove the reload (REQ-HARNESS-009) tagged `@req REQ-HARNESS-009`; verify by typecheck and a manual run on a scratch project where a write to an existing change's folder binds it
