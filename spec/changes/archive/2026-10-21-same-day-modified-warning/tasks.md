# Tasks: same-day-modified-warning

## 1. The close time in History

- [x] 1.1 Write a failing test in `tests/test_close_phase.py` for AC-SPECS-013.5 (a close's History line holds the date and a `HH:MM:SS` time, earlier lines unchanged) tagged `@ac`; verify it fails because the line holds only the date
- [x] 1.2 In `plan_merge`, stamp the History line with the local date and time (REQ-SPECS-013) tagged `@req REQ-SPECS-013`; verify the 1.1 test and the existing AC-SPECS-013.x tests pass

## 2. The warning compares times

- [x] 2.1 Write failing tests in `tests/test_propose.py` for AC-SPECS-006.7 (a line timed before the start doesn't warn; one timed after, or holding only the day, does) tagged `@ac`; verify the "before" case fails because it warns
- [x] 2.2 In `modified_since`, read the optional time and compare by time when both sides have one, else by day (REQ-SPECS-006) tagged `@req REQ-SPECS-006`; verify the 2.1 tests and the existing AC-SPECS-006.5 test pass
