# Spec Delta: cli

## MODIFIED Requirements

### Requirement: REQ-CLI-019 A change's telemetry IDs

`status --json` SHALL show, for an active or archived change, `telemetry`
with its `traceId` and `sessionId` (REQ-PROJ-031), whether or not telemetry
is opted in. For a change in a module, `sessionId` SHALL be the change's
module-qualified ref.

#### Scenario: AC-CLI-019.1 The IDs

- **GIVEN** a change `add-login`
- **WHEN** `status --change add-login --json` runs, before and after it is archived
- **THEN** both show `telemetry` with the same `traceId` and `sessionId` `add-login`

#### Scenario: AC-CLI-019.2 A change in a module

- **GIVEN** a change `cleanup` at the top level and a change `cleanup` in module `billing`, created at the same time
- **WHEN** `status --change billing:cleanup --json` and `status --change cleanup --json` run
- **THEN** the first shows `sessionId` `billing:cleanup`, the second `cleanup`, and their `traceId` values differ
