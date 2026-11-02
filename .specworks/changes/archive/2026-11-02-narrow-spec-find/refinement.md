# Refinement: narrow-spec-find

## Problem

`specworks spec find` matches a term on any line of a requirement's block,
the spec's own markup included: `### Requirement:`, `#### Scenario:` and the
bold `GIVEN`/`WHEN`/`THEN`. So `requirement`, `scenario`, `when` and `then`
match all 81 living requirements, and specify's step 2, which asks for a
decision on every match, gets buried in noise. So far it was avoided only by
picking narrow terms.

## Outcomes

- A term found only in the spec markup no longer matches: on today's living
  specs, `requirement` goes from 81 to 21 matches and `scenario` from 81 to 3.
- A term still matches in a requirement's title, text and scenarios' text,
  and its ID stays searchable: the terms used in the archived proposals find
  the same requirements as before.
- When a term matches more than half of the living requirements, `spec find`
  warns that it is too broad, naming it, so specify picks a narrower one.

## Context

**Observed:**
- `find_requirements` in `src/specworks/specs/capabilities.py` checks each
  line of a requirement's block, from its `### Requirement:` line to its end,
  for any term (literal, ignoring case), and reports the first matching line.
  `spec find` in `src/specworks/cli/specs.py` prints the matches.
- `specs` REQ-SPECS-016 (finding living requirements by term) and `cli`
  REQ-CLI-016 (`spec find`), living docs in `src/specworks/specs/docs/` and
  `src/specworks/cli/docs/`.
- Measured on the 81 living requirements, today vs. with the markup keywords
  removed: `requirement` 81 → 21, `scenario` 81 → 3, `when` 81 → 47,
  `then` 81 → 16, `given` 53 → 10; `shall` 81 and `system` 42 are unchanged
  (words of the descriptions), as are `finding`, `back to` and `gate code`.
- Whole-word matching would narrow `spec` (53 → 18) but loses `branch` in
  `--no-branch` and `finding` in `findings`.

**Assumed:**
- Nobody searches for the markup keywords on purpose.

## Constraints

- [hard] Matching stays literal and ignores case; the output keeps the first
  matching line and its number.
- [hard] A requirement's ID (in its header) and its scenarios' IDs stay searchable.
- [soft] The broad-term threshold is fixed (more than half), not configured.

## Options

### Option A: remove the markup keywords, then match

Before comparing, drop from each line the `### Requirement:` and
`#### Scenario:` keywords and the bold `GIVEN`/`WHEN`/`THEN`/`AND` labels,
keeping the IDs and every other word. The warning is computed with the
matches and shown as text and under `--json`.

- **Pros:** one pattern; line numbers and output unchanged.
- **Cons:** the markup keywords are listed in one place and must follow the spec format.
- **Effort:** S
- **Touches:** `specs`, `cli`
- **Outcomes:** meets all three.

### Option B: match the parsed fields

Match against `parse_spec`'s `Requirement` and `Scenario` (title,
description, scenario title and steps) instead of raw lines.

- **Pros:** follows the spec's structure.
- **Cons:** line numbers have to be carried per field; parse edge cases A does not need.
- **Effort:** M
- **Touches:** `specs`, `cli`
- **Outcomes:** meets all three.

### Option C: a broad-term warning only

Keep matching as it is and warn on every term that matches more than half.

- **Pros:** smallest.
- **Cons:** `requirement` and `when` still list all 81, with a warning every time.
- **Effort:** S
- **Touches:** `specs`, `cli`
- **Outcomes:** meets the second and third; fails the first.

## Recommendation

Option A, agreed with the user: it meets all three outcomes with the smallest
change and keeps the output as it is.

## Open Questions

- None. Out of scope: whole-word matching, ranking the matches, a configurable
  threshold, searching delta specs of active changes.

## Candidate Capabilities

- `specs`: modified - REQ-SPECS-016 (markup does not match; broad terms reported).
- `cli`: modified - REQ-CLI-016 (`spec find` prints the warning, and lists the broad terms under `--json`).
