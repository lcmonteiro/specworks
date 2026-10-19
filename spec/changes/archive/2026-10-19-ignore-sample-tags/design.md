# Design: ignore-sample-tags

## Context

`scan_tags` (`src/specworks/specs/trace.py`) reads every scanned file line by line
and matches `TAG_RE` anywhere on a line. Every check (trace matrix, gaps, unknown
tags, review, validate) works from the list of tags it returns. See proposal.md
for the motivation.

## Goals / Non-Goals

**Goals:**
- Skip marked lines inside `scan_tags`, so that every consumer leaves ignored tags
  out without any change of its own (REQ-SPECS-003).
- Keep the markers language-agnostic: plain text matched anywhere on a line.

**Non-Goals:**
- Counting or reporting ignored tags.
- Recognising comments or string literals.

## Decisions

### Filter in the scan, not in the checks

`scan_tags` skips ignored lines before it builds any `Tag`. The alternatives were
an `ignored` flag on `Tag` that every check would have to respect, or a filter in
`unknown_tags` only. Both are riskier: a check that forgets the flag would count
a sample as coverage. Serves: REQ-SPECS-003.

### One line-state pass per file

For each file that holds a tag, a small pass walks its lines with an "inside a
block" flag:
- A line whose text, once `specworks: ignore-tags-start` is removed, has no
  letters or digits opens a block. The same goes for `-end`, which closes one.
  An end with no open block does nothing. The marker lines themselves are
  skipped.
- A line inside a block is skipped. At the end of the file the flag is dropped,
  so a block never reaches the next file.
- Outside a block, a line matching `specworks: ignore-tags(?!-)` is skipped.

The rule for a line with no other letters or digits is what lets docs quote a
marker without triggering it. It accepts `#`, `//`, `--`, `/* */`, `<!-- -->`
and `;` comments alike. Serves: REQ-SPECS-001, REQ-SPECS-002.

## Interfaces

None. `scan_tags(ws) -> list[Tag]` keeps its signature. The marker handling is a
private helper in `src/specworks/specs/trace.py`.

## Risks / Trade-offs

- [A stray start marker silently hides real tags up to the end of the file] ->
  Those tags then show up as missing coverage in `trace` and the gates, so the
  hole is visible. A warning for an unclosed block is a possible follow-up.
- [A project already has the text `specworks: ignore-tags` on a tagged line] ->
  Very unlikely. The marker is specific to specworks.
