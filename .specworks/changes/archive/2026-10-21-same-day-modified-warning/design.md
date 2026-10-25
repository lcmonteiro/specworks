# Design: same-day-modified-warning

## Decisions

### The History line holds the close time; old lines compare by day

`plan_merge` stamps its History line with the local date and time to the second
(`2026-10-21 09:14:02`), the format a change's `created` already uses, with a
space instead of the `T`. `HISTORY_LINE_RE` takes an optional time after the
date. `modified_since` keeps a line when its stamp is on or after the change's
start: when both the line and the start have a time, by date and time; when
either has only a day, by day, as today. A close in the same second as the start
still warns, so no close after the start is missed. Serves: REQ-SPECS-006,
REQ-SPECS-013.

## Interfaces

- `src/specworks/specs/merge.py`: `plan_merge(ws, change, specs, change_ref, today=None)`
  keeps its signature; `today` (for tests) may now hold a time
  (`"2026-10-21 09:14:02"`), and defaults to the current local date and time.
- `src/specworks/specs/capabilities.py`: `modified_since(cap, since)` keeps its
  signature and return value.
