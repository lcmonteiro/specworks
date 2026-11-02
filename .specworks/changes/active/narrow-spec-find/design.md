# Design: narrow-spec-find

## Context

`find_requirements(ws, terms)` in `src/specworks/specs/capabilities.py` checks
each line of a requirement's block for any term and stops at the first;
`spec find` in `src/specworks/cli/specs.py` prints the list. See proposal.md
for why.

## Goals / Non-Goals

**Goals:**
- The markup is removed in one place, before comparing, for every term.
- The broad terms come from the same scan as the matches, so they always agree.

**Non-Goals:**
- Changing what a match is (first matching line) or the order of the matches.

## Decisions

### Removing the markup

A private pattern drops, at the start of a line, `### Requirement:` (keeping
the ID and title after it), `#### Scenario:` (keeping the AC ID and title),
and a step's bullet with its bold label (`- **GIVEN**`, `**WHEN**`,
`**THEN**`, `**AND**`, any case), keeping the step's text. The term is
compared with what is left, and the reported `text` stays the whole stripped
line as today. Only line starts are touched, so a bold `**WHEN**` quoted inside
a requirement's text still matches. Serves: REQ-SPECS-016.

Alternative: matching `parse_spec`'s fields (option B in refinement.md),
rejected for the line numbers it would have to carry.

### Broad terms

Each term counts the requirements it matches in the same scan (a requirement
counts once per term, even when its first matching line was found by another
term). A term is broad when its count is more than half of the living
requirements searched (`count * 2 > searched`); none is broad when no
requirement is searched. The threshold is fixed. Serves: REQ-SPECS-016.

### The CLI

The text output lists the matches as today, then one line per broad term:
`warning: '<term>' matches <n> of <m> requirements; try a narrower term`.
It still exits 0. `--json` adds `"broad": [{"term", "matches", "of"}]`, empty
when no term is broad. With no match at all, the text is still
`no requirement mentions <terms>`. Serves: REQ-CLI-016.

## Interfaces

Agreed with the user

- `src/specworks/specs/capabilities.py`: `search_requirements(ws, terms) -> RequirementSearch`
  (REQ-SPECS-016), raising `ConfigError(f"empty search term: {term!r}")` for
  the first blank term, as `find_requirements` does.
- `src/specworks/specs/capabilities.py`: `RequirementSearch` dataclass:
  `matches: list[RequirementMatch]`, `broad: list[BroadTerm]` (in the order
  of the terms), `searched: int` (living requirements searched).
- `src/specworks/specs/capabilities.py`: `BroadTerm` dataclass: `term: str`
  (as given), `matches: int`, `of: int`.
- `src/specworks/specs/capabilities.py`: `find_requirements(ws, terms) -> list[RequirementMatch]`
  (extended, not breaking): same signature, now returns
  `search_requirements(ws, terms).matches`, so the markup no longer matches.
- `src/specworks/cli/specs.py`: `spec find` (extended, not breaking): same
  arguments; prints `warning: '<term>' matches <n> of <m> requirements; try a
  narrower term` per broad term, and `--json` adds
  `broad: [{"term", "matches", "of"}]`, existing keys unchanged (REQ-CLI-016).

## Diagrams

No structural change.

## Risks / Trade-offs

- [a markup keyword someone searches on purpose no longer matches] -> its IDs
  and titles still do; nobody searched for them in the archived proposals.
- [the warning fires for a term that is broad but right] -> it is a warning:
  the matches are still listed and the exit code is 0.

## Open Questions

None.
