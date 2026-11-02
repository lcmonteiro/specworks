# Proposal: narrow-spec-find

## Why

`spec find` matches the markup every requirement has (`### Requirement:`,
`#### Scenario:`, the bold `GIVEN`/`WHEN`/`THEN`), so `requirement`,
`scenario`, `when` and `then` match all 81 living requirements and specify's
step 2 has to decide on every one (refinement.md, option A).

## What Changes

- A term no longer matches the spec's markup: the `Requirement:` and
  `Scenario:` keywords of the headings and the bold `GIVEN`, `WHEN`, `THEN`
  and `AND` of the steps are left out before comparing. Everything else on a
  line still matches: a requirement's ID and title, its text, a scenario's ID,
  title and steps.
- A term that matches more than half of the living requirements searched is
  reported as broad: `spec find` prints a warning naming it, with how many of
  how many it matched, and lists it under `broad` in `--json`. The matches are
  still listed.
- Matching stays literal and ignoring case, and each match keeps its first
  matching line and number.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `specs`: REQ-SPECS-016 Finding living requirements by term (markup does not
  match; broad terms are reported).
- `cli`: REQ-CLI-016 spec find (the broad-term warning, and `broad` under `--json`).

## Related requirements

Found with `specworks spec find "spec find" find_requirements "search term" "matching line"`:

- REQ-SPECS-016 modified
- REQ-CLI-016 modified
- REQ-FLOW-012 left: it matched "spec find" inside "spec finding"; build cycles do not search requirements

## Impact

- `src/specworks/specs/capabilities.py` (`find_requirements` and what it
  returns), `src/specworks/cli/specs.py` (`spec find`).
- Tests in `tests/` for both requirements.
- `--json` of `spec find` gains a `broad` key; existing keys are unchanged.

## Out of Scope

- Whole-word matching, ranking the matches, a configurable threshold.
- Searching the delta specs of active changes.
- The specify skill's wording (it already reads the matches and decides each one).
