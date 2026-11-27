# Refinement: skip-abandoned-inspections

## Problem

`pr-review-with-inspect` shows an archived change's open inspection notes by
turn, and points the author to `/specworks-reopen`. An abandoned change is
archived too, so one with open notes would be listed in `context`'s
`inspected` and in `status` / `list --archived` with a reopen hint, while
reopen refuses abandoned changes ("start a new change instead"). Raised as
the one warning of that change's validate.

## Outcomes

- For an abandoned change with open inspection notes, `status --json` and
  its `list --archived` row have no `inspection`, and their text shows no
  inspection hint.
- `context`'s `inspected` never lists an abandoned change.
- Closed (not abandoned) changes behave exactly as today.
- inspection.md's artifact state (`open` / `done`) is unchanged: it states a
  fact about the file, whatever the change's fate.

## Context

**Observed:**
- `core/changes.py:247-248`: reopen raises for an abandoned change (`was
  abandoned (...), not closed: start a new change instead`).
- `core/changes.py:180` `list_archived` returns closed and abandoned changes;
  `Change.abandoned` holds the reason (empty when closed).
- `cli/output.py:78` `inspection_dict` checks only `is_archived`; `status`
  (`cli/changes.py:93`) and `list --archived` (`cli/project.py:306`) use it.
- `cli/project.py:248`: `context`'s `waiting` calls `inspection_turns` on
  every archived change directly, not through `inspection_dict`.
- Living requirements REQ-CLI-025 ("an archived change"), REQ-CLI-026,
  REQ-CLI-027 ("the archived changes ... that have open inspection notes").
- The repository has no abandoned change; none was ever inspected.

**Assumed:**
- Notes on an abandoned change have no one to act on them, so hiding them
  loses nothing a person needs; they stay readable in inspection.md.

## Constraints

- [hard] Stacked on `pr-review-with-inspect` (not yet on `main`).
- [hard] No change to reopen, inspect's routing, or the artifact states.
- [soft] One rule shared by the three commands, so they cannot drift.

## Options

### Option A: One rule in `inspection_dict`, reused by `context`

`inspection_dict` returns nothing for an abandoned change; `context` builds
`inspected` from it instead of calling `inspection_turns` itself.

- **Pros:** one place decides; `context` and `status` cannot disagree.
- **Cons:** `context` changes how it builds its list (small).
- **Effort:** S
- **Touches:** cli
- **Outcomes:** meets all four.

### Option B: Filter each command

Add `not c.abandoned` in `inspection_dict` and again in `context`'s list.

- **Pros:** the smallest diff.
- **Cons:** two conditions to keep in step.
- **Effort:** S
- **Touches:** cli
- **Outcomes:** meets all four today; the next command risks missing it.

## Recommendation

Option A. Not recommended as a full change on its own merits: the case is
hypothetical (no abandoned change exists here). The user reshaped it to this
minimal fix rather than a new hint for abandoned changes or no change.

## Open Questions

None.

## Candidate Capabilities

- `cli`: modified - REQ-CLI-025, REQ-CLI-026 and REQ-CLI-027 say a closed,
  not abandoned, change.
