# Review: diagram-bad-svg

Base: `origin/main`

## Findings

- [x] R1 **spec-gap** AC-INTEG-003.4 promises `cannot render <name>.d2: …` when d2 writes no SVG, but pyd2 already reports that case itself, as `d2 failed on <name>.d2: no SVG was written to …` (no crash, diagram named), like a compile error (REQ-INTEG-003, AC-INTEG-003.4; `tests/test_diagrams.py`)
  - **Decision**: back to specify: narrow AC-INTEG-003.4 to the unclosed declaration and non-UTF-8 output (`cannot render …`), and state that no SVG at all is reported with d2's own message naming the diagram; the test then expects that message (agreed with the user)
  - done in specify: AC-INTEG-003.4 now promises `cannot render …` for the unclosed declaration and non-UTF-8 output, and d2's own `no SVG was written` message for no output; proposal and tasks 1.1/1.2 updated
  - **Resolved** in cycle 2: the test expects d2's message for no SVG; `render` lost its dead `FileNotFoundError` branch (pyd2 reports a missing SVG before `render` reads it)

## Changed files without tags

- `tests/helpers.py`: only `specworks: ignore-tags` markers from ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

Checked against REQ-INTEG-003 (MODIFIED) after cycle 2:
- AC-INTEG-003.4: `stamp` raises a clear `ValueError` for an unclosed
  `<?xml` declaration, and `render` turns it, non-UTF-8 output and any other
  read or write error into `cannot render <name>.d2: …`. The test renders a
  good diagram next to three bad ones and checks each result: the good one is
  rendered, the unclosed and non-UTF-8 ones get `cannot render`, the missing
  one gets d2's `no SVG was written`, and the exit code is 1. Against the code
  on `origin/main` the test fails with the crash.
- AC-INTEG-003.1 to .3 still pass. All 28 tests in `tests/test_diagrams.py`
  pass, and so do the full suite and lint.

## Summary

An SVG that can't be stamped is now a render error naming the diagram, not a
crash, and the rest of the run still renders. R1 corrected the spec where pyd2
already reported a missing SVG.
