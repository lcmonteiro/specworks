# Tasks: run-unknown-key

## 1. Unknown and unconfigured command keys

- [ ] 1.1 Write failing tests in `tests/test_code_phase.py` for AC-PROJ-013.4 (`run frobnicate` names the valid keys and doesn't say "add it under commands:") and extend the AC-PROJ-013.3 test to check the example uses `lint`, tagged `@ac`; verify they fail on today's message
- [ ] 1.2 In `run_command`, refuse a key outside `COMMAND_KEYS` listing them, and give the unconfigured message an example for the key asked for (REQ-PROJ-013) tagged `@req REQ-PROJ-013`; verify the 1.1 tests and the existing AC-PROJ-013.x and gate tests pass
