# Proposal: skip-abandoned-inspections

## Why

An abandoned change is archived like a closed one, so with open inspection
notes it would be shown with `/specworks-reopen`, which refuses abandoned
changes. The validate of `pr-review-with-inspect` warned about it. The case
is hypothetical (no abandoned change exists here), so the fix stays minimal.

## What Changes

- `status`, `list --archived` and `context`'s `inspected` report inspection
  notes only for a closed change, never for an abandoned one: no
  `inspection` key, no inspection hint, not listed in `inspected`.
- One rule decides it, shared by the three commands.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `cli`: REQ-CLI-025, REQ-CLI-026, REQ-CLI-027 say a closed, not abandoned,
  change.

## Related requirements

- REQ-CLI-025, REQ-CLI-026, REQ-CLI-027 modified: only a closed change's
  notes are shown.
- REQ-FLOW-001 left: inspection.md's `open` / `done` state describes the
  file, whatever the change's fate.
- REQ-FLOW-020 left: reading notes by turn is unchanged.
- REQ-PROJ-033, REQ-CLI-020 left: reopen still refuses abandoned changes.
- REQ-CLI-006 left: `abandon` is unchanged.
- REQ-PROJ-020, REQ-PROJ-030, REQ-CLI-002 left: matched on "abandoned" in an
  unrelated sense (where changes live, the event log, naming).

## Impact

- `src/specworks/cli/output.py` (`inspection_dict`) and
  `src/specworks/cli/project.py` (`context`'s `inspected`).
- No JSON shape change: keys are only absent for abandoned changes.

## Out of Scope

- A hint of its own for abandoned changes (e.g. start a new change).
- Changing reopen, inspect, or the inspection artifact state.
