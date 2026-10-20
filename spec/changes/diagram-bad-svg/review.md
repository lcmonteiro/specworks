# Review: diagram-bad-svg

Base: `origin/main`

## Findings

- [ ] R1 **spec-gap** AC-INTEG-003.4 promises `cannot render <name>.d2: …` when d2 writes no SVG, but pyd2 already reports that case itself, as `d2 failed on <name>.d2: no SVG was written to …` (no crash, diagram named), like a compile error (REQ-INTEG-003, AC-INTEG-003.4; `tests/test_diagrams.py`)
  - **Decision**: back to specify: narrow AC-INTEG-003.4 to the unclosed declaration and non-UTF-8 output (`cannot render …`), and state that no SVG at all is reported with d2's own message naming the diagram; the test then expects that message (agreed with the user)
  - done in specify: AC-INTEG-003.4 now promises `cannot render …` for the unclosed declaration and non-UTF-8 output, and d2's own `no SVG was written` message for no output; proposal and tasks 1.1/1.2 updated

## Changed files without tags

- `tests/helpers.py`: only `specworks: ignore-tags` markers from ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

Found while coding: the refinement assumed a missing SVG crashes, but pyd2
already reports it. The spec goes back to specify for that one case.
