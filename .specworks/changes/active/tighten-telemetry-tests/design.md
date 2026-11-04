# Design: tighten-telemetry-tests

## Context

The change only tightens two checks of behaviour that already exists
(see [proposal.md](proposal.md)): the 7 s bound of AC-INTEG-009.3 against the
5 s timeout in `src/specworks/integrations`, and the module-qualified
`sessionId` built by `telemetry_ids` in `src/specworks/cli/telemetry.py`
(AC-CLI-019.2). No source code changes.

## Interfaces

None: no class, function, command or data shape is added or extended;
`telemetry_ids` and the langfuse send already exist and keep their signatures,
so there are no stubs to create.

## Diagrams

No structural change.
