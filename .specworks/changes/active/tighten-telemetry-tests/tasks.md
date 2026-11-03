# Tasks: tighten-telemetry-tests

## 1. Sending: the timeout bound

- [ ] 1.1 [test] Tighten the test for AC-INTEG-009.3 in `tests/integrations/test_langfuse.py` to assert `elapsed < 7`, tagged `@ac AC-INTEG-009.3` (REQ-INTEG-009, AC-INTEG-009.3); verify `uv run pytest tests/integrations/test_langfuse.py -k 009_3` passes against the existing 5 s timeout

## 2. Status: the module-qualified session ID

- [ ] 2.1 [test] Write the test for AC-CLI-019.2 in `tests/cli/test_telemetry.py`, tagged `@ac AC-CLI-019.2`: a change `cleanup` at the top level and one in module `billing` created at the same time; `status --json` shows `sessionId` `billing:cleanup` and `cleanup` and different `traceId` values (REQ-CLI-019, AC-CLI-019.2); verify `uv run pytest tests/cli/test_telemetry.py -k 019_2` passes against the existing code

## Workflow follow-up

- No `[code]` task: the behaviour already exists (`telemetry_ids` in `src/specworks/cli/telemetry.py`); the change adds checks only, so `specworks check` warns about it.
