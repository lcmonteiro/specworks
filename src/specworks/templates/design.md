# Design: <!-- change name -->

## Context

<!-- Current state and constraints. See proposal.md for motivation; don't restate it. -->

## Goals / Non-Goals

**Goals:**
- <!-- design-level goal -->

**Non-Goals:**
- <!-- explicitly excluded -->

## Decisions

### <!-- decision -->

<!-- What, why, alternatives considered. Serves: REQ-... -->

## Interfaces

<!-- Public APIs, data shapes, events, CLI surfaces added or extended, each with its file:
- `src/auth/reset.py`: `ResetService.request_reset(email: str) -> None` (REQ-...)
Settled in the design phase; "None" when the API does not change. -->

## Diagrams

<!-- A change that adds, removes or moves components, or changes the dependencies between them,
gets one block diagram per capability whose structure changes, of that structure after it,
named diagrams/<capability>-blocks.d2; otherwise write "No structural change".
Other diagrams (flows, states, tables) are optional.
Write diagrams/<name>.d2, run `specworks diagrams --change <ref>`, then embed:
![Password reset flow (REQ-AUTH-003)](diagrams/reset-flow.svg)
-->

## Risks / Trade-offs

- <!-- [risk] -> mitigation -->

## Migration / Rollback

<!-- Only if deployment or data needs steps -->

## Open Questions

<!-- Only questions that don't change specs, approach or tasks -->
