# Design: fix-commit-after-close

## Context

See proposal.md. `specworks commit` (`src/specworks/cli/changes.py`) finds
the change with `require_change`, active only; `archived_as(cfg, name)` in
`src/specworks/core/changes.py` finds the newest archived one. After close an
archived change's phase is `done`.

## Goals / Non-Goals

**Goals:**
- The close and done skills' commit works as written.

**Non-Goals:**
- Committing an older archived change on purpose.

## Decisions

### Fall back to the archived change in the command

`commit` looks up the active change first and, only when there is none,
`archived_as` in the same module; neither found is the existing unknown
change error. `commit_phase` is unchanged in signature: for a change in
phase `done` its default subject is `<ref>: close`, and `already_dirty`
skips paths under the change's folder. Serves REQ-PROJ-024, REQ-CLI-012.

### Pinned wording

- Subject of an archived change: `<ref>: close`

## Interfaces

None: no signature changes; `commit` finds one more kind of change and
`commit_phase` gets one more default.

## Diagrams

No structural change.
