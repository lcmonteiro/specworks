# Proposal: diagram-bad-svg

## Why

When d2 succeeds but writes an SVG specworks can't stamp (an unclosed XML
declaration, no output file, or output that isn't UTF-8), `specworks diagrams`
crashes with a traceback and skips the rest of the run (reproduced; suspected
bug 8 of `baseline-integrations`; refinement.md, option A).

## What Changes

- Reading and stamping the SVG d2 wrote join the render's error handling. Each
  of those cases is reported as `cannot render <name>.d2: …` for that diagram.
  The other diagrams still render, and the command exits 1.
- A well-formed SVG is stamped exactly as today.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `integrations`: REQ-INTEG-003 "The d2 that renders" MODIFIED. Its description
  adds an SVG that can't be read or stamped to the reported errors, and it gets
  a new criterion, AC-INTEG-003.4.

## Impact

`src/specworks/tools/diagrams.py` (`render`, `stamp`) and
`tests/test_diagrams.py`. No API, data or dependency change.

## Out of Scope

- Validating the SVG beyond what stamping needs.
- Removing a broken SVG left by a failed render (as after a compile error, it
  stays, and its state reads `stale`).
