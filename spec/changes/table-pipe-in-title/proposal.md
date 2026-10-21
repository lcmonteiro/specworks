# Proposal: table-pipe-in-title

## Why

A `|` in a requirement or criterion title splits its cell in the tables
specworks generates, so requirements.md and traceability.md render with extra
columns (reproduced; suspected bug of `baseline-specs`; refinement.md,
option A).

## What Changes

- Every title written into a generated table cell has its `|` escaped as `\|`:
  the requirements.md index, and the matrix and Removed tables of
  traceability.md. On GitHub the title shows as written.
- spec.md and titles elsewhere (History lines, CLI output, JSON) are unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `specs`: REQ-SPECS-012 "The trace matrix" MODIFIED (new criterion
  AC-SPECS-012.5) and REQ-SPECS-013 "Merging at close" MODIFIED (new criterion
  AC-SPECS-013.6).

## Impact

`src/specworks/specs/merge.py` (`requirements_index`),
`src/specworks/specs/trace.py` (`to_markdown`) and their tests. No API, data or
dependency change.

## Out of Scope

- Refusing or warning about `|` in titles (options B and C).
