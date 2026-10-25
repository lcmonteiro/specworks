# Refinement: same-day-modified-warning

## Problem

`check` warns that a MODIFIED requirement "was MODIFIED by <other> on <date>,
after this change started" when the other change closed earlier on the same day,
before this one started. Seen twice on 2026-10-20 (`module-outside-workspace`,
after `module-add-nested` had closed). The false warning teaches users to
ignore a warning that guards against undoing another change's edits. Found as
a suspected bug of `baseline-specs`.

## Context

**Observed:**
- `specs/capabilities.py`, `modified_since(cap, since)`: cuts `since` to its
  day and keeps every History line whose date is on or after it.
- `specs/merge.py`, `plan_merge`: writes History lines as
  `- <YYYY-MM-DD> \`<change>\`: <summary>`, the day only.
- `core/changes.py`: a change's `created` is a local time to the second
  (`2026-10-20T23:22:57`).
- Living spec: `specs` REQ-SPECS-006 (the warning, AC-SPECS-006.5) and
  REQ-SPECS-013 (requirements.md and its History).

**Assumed:**
- Close and `new` run on clocks close enough that local times compare.

## Constraints

- [hard] A close after this change started always warns: missing one undoes
  another change's edits.
- [hard] Existing History lines (day only) keep working.
- [soft] requirements.md stays readable and its History one line per close.

## Options

### Option A: The close time in History

Close writes the time on each new History line
(`- 2026-10-20 22:41:07 \`x\`: MODIFIED ...`), and `check` compares it with the
change's start time. A line with a day only keeps today's comparison by day.

- **Pros:** Exact for every new close; no other file read; old lines still warn.
- **Cons:** A small format change in requirements.md.
- **Effort:** S
- **Touches:** `specs`

### Option B: The close time in the archive

- **Pros:** History unchanged.
- **Cons:** `check` would read every archived change; a pruned archive breaks it.
- **Effort:** M
- **Touches:** `specs`, `project`

### Option C: Only reword the warning

- **Pros:** Smallest.
- **Cons:** The false warning stays.
- **Effort:** S
- **Touches:** `specs`

## Recommendation

**Option A**, chosen with the user.

## Open Questions

None.

## Candidate Capabilities

- `specs`: REQ-SPECS-013 MODIFIED (History lines carry the close time) and
  REQ-SPECS-006 MODIFIED (the warning compares times when the line has one).
