# Review: table-pipe-in-title

Base: `origin/main`

## Findings

- [ ] R1 **tag** `table_cell` was inserted between `# @req REQ-SPECS-004` and `living_problems`, so that tag now sits on `table_cell` and `living_problems` lost it; the gate passes only because REQ-SPECS-004 has other code (`src/specworks/specs/specfile.py:249`)
  - **Decision**: back to code: move `# @req REQ-SPECS-004` back onto `living_problems`

## Changed files without tags

None: every changed file has tags.

## Summary

`table_cell` escapes `|`, and `requirements_index` and `to_markdown` pass every
title through it (AC-SPECS-012.5, AC-SPECS-013.6). No other generated table
puts a title in a cell. One tag was displaced by the new function (R1), back
to code.
