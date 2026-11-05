# Proposal: tighten-telemetry-tests

## Why

Validating `add-langfuse-monitoring` passed with two warnings: AC-INTEG-009.3's
test allows 10 s although the code times out after 5 s, and the module-qualified
session ID built in the CLI (`billing:cleanup`) has no test. Both let a regression
pass unnoticed.

## What Changes

- AC-INTEG-009.3 says the send returns within 7 seconds, and its test asserts `elapsed < 7`.
- A new scenario AC-CLI-019.2 checks `status` for a change in module `billing`: its `sessionId` is `billing:cleanup` and its `traceId` differs from a top-level change of the same name and creation time.
- No behaviour of the CLI changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `integrations`: REQ-INTEG-009 (scenario AC-INTEG-009.3 reworded).
- `cli`: REQ-CLI-019 (scenario AC-CLI-019.2 added).

## Related requirements

- REQ-INTEG-009 modified
- REQ-CLI-019 modified
- REQ-PROJ-031 left: unchanged; the module-qualified path is covered by AC-CLI-019.2
- REQ-PROJ-030 left: the event log is not touched
- REQ-PROJ-024 left: committing is not touched
- REQ-CLI-018 left: `telemetry push` is not touched
- REQ-CLI-002 left: naming a change is not touched
- REQ-FLOW-001 left: artifact states are not touched

## Impact

- Tests: `tests/integrations/test_langfuse.py`, `tests/cli/test_telemetry.py`.
- Specs: `integrations`, `cli`.
- No source code, API or data change.

## Out of Scope

- The session ID in the sending path (`_send`).
- The REQ-PROJ-025 long-description warning (accepted earlier).
- Any change to the 5 s timeout itself.
