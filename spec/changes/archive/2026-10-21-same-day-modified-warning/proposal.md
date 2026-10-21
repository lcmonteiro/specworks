# Proposal: same-day-modified-warning

## Why

`check` warns that a MODIFIED requirement was changed by another change "after
this change started" when that change closed earlier the same day, because
requirements.md's History records only the day. The false warning teaches users
to ignore a check that guards against undoing another change's edits
(suspected bug of `baseline-specs`; refinement.md, option A).

## What Changes

- Close writes the local time on each new History line of requirements.md:
  `- 2026-10-20 22:41:07 \`<change>\`: <summary>`.
- `check` compares a History line that has a time with the change's start
  time, so a close before it started no longer warns. A line with only a day
  keeps today's comparison by day.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `specs`: REQ-SPECS-013 "Merging at close" MODIFIED (History lines carry the
  close time, new criterion AC-SPECS-013.5) and REQ-SPECS-006 "A delta against
  its living spec" MODIFIED (the warning compares times, new criterion
  AC-SPECS-006.7).

## Impact

`src/specworks/specs/merge.py` (`plan_merge`), `src/specworks/specs/capabilities.py`
(`modified_since`, `HISTORY_LINE_RE`) and their tests. requirements.md History
lines written from now on hold a time; existing lines are left as they are.

## Out of Scope

- Rewriting existing History lines.
- Time zones: `new` and `close` both use the local clock.
