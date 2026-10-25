# Refinement: table-pipe-in-title

## Problem

A requirement or criterion title holding `|` breaks the markdown tables
specworks generates. Reproduced: a requirement titled `Read | write` becomes the
requirements.md row `| REQ-X-001 | Read | write | AC-X-001.1 |`, four cells
under a three-column header, so the index renders wrong. traceability.md puts
requirement and criterion titles in table cells the same way. Found as a
suspected bug of `baseline-specs`.

## Context

**Observed:**
- `specs/merge.py`, `requirements_index`: `| {req.id} | {req.title} | {acs} |`.
- `specs/trace.py`, `to_markdown`: requirement and criterion titles in the
  matrix and in the Removed table.
- Nothing parses these tables back; `history_lines` reads only the History
  list.
- Living spec: `specs` REQ-SPECS-012 (the trace matrix) and REQ-SPECS-013
  (requirements.md).

**Assumed:**
- Readers view these files on GitHub or in an editor that follows GitHub
  markdown, where `\|` in a table cell shows a literal `|`.

## Constraints

- [hard] A title shows as written, whatever characters it holds.
- [soft] spec.md is not constrained further.

## Options

### Option A: Escape `|` in generated table cells

- **Pros:** Titles keep any character; one helper for both files.
- **Cons:** The raw file shows `\|`.
- **Effort:** S
- **Touches:** `specs`

### Option B: Refuse `|` in titles

- **Pros:** Simplest.
- **Cons:** Forbids a character that is fine in spec.md.
- **Effort:** S
- **Touches:** `specs`

### Option C: Both, with a warning

- **Pros:** Escaped, and the author is told.
- **Cons:** A warning about something already handled.
- **Effort:** S
- **Touches:** `specs`

## Recommendation

**Option A**, chosen with the user.

## Open Questions

None.

## Candidate Capabilities

- `specs`: REQ-SPECS-012 and REQ-SPECS-013 MODIFIED: a `|` in a title is
  escaped in the tables of traceability.md and requirements.md.
