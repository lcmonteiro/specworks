# Design: skip-abandoned-inspections

## Context

See proposal.md. `inspection_dict` (`src/specworks/cli/output.py`) decides
whether `status` and `list --archived` carry `inspection`; `context`
(`src/specworks/cli/project.py`) builds `inspected` by calling
`inspection_turns` on every archived change itself.

## Goals / Non-Goals

**Goals:**
- One rule, in one place, decides whether a change's notes are shown.

**Non-Goals:**
- No hint for abandoned changes; no change to workflow, reopen or inspect.

## Decisions

### `inspection_dict` is the one rule, and `context` uses it

`inspection_dict(change)` returns `{}` for an abandoned change (non-empty
`Change.abandoned`) as it already does for an active one. `context` builds
`inspected` from the archived changes whose `inspection_dict` is not empty,
instead of calling `inspection_turns` itself, so the three commands cannot
disagree. Alternative: add `not c.abandoned` in both places; rejected, two
conditions to keep in step. Serves: REQ-CLI-025, REQ-CLI-026, REQ-CLI-027.

`context`'s text line still needs the turns for `inspection_hint`; it reads
them from `inspection_turns` only for the changes `inspection_dict` kept.

## Interfaces

None: `inspection_dict(change: Change) -> dict` keeps its signature
(`src/specworks/cli/output.py`); only its result for an abandoned change
changes (REQ-CLI-025).

## Diagrams

No structural change.

## Risks / Trade-offs

- [`context` reads each kept change's inspection.md twice] -> only changes
  with open notes, a handful at most.

## Open Questions

None.
