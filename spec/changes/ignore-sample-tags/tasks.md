# Tasks: ignore-sample-tags

## 1. Line marker

- [ ] 1.1 Write failing tests for AC-SPECS-001.1, AC-SPECS-001.2 (scan a marked line in `#` and `//` syntax) tagged `@ac`; verify they fail because the marked tags are still found
- [ ] 1.2 Skip the tags on lines holding `specworks: ignore-tags` in `scan_tags` (REQ-SPECS-001) tagged `@req REQ-SPECS-001`; verify the 1.1 tests pass

## 2. Block markers

- [ ] 2.1 Write failing tests for AC-SPECS-002.1, AC-SPECS-002.2, AC-SPECS-002.3, AC-SPECS-002.4 tagged `@ac`; verify they fail because the tags inside blocks are still found
- [ ] 2.2 Skip the lines from a start to an end marker, counting a marker only on a line with no other letters or digits (REQ-SPECS-002) tagged `@req REQ-SPECS-002`; verify the 2.1 tests pass and 1.1 still passes

## 3. Ignored tags in the checks

- [ ] 3.1 Write tests for AC-SPECS-003.1, AC-SPECS-003.2 (`trace --change` with an ignored unknown-prefix tag, and a criterion whose only `@ac` is ignored) tagged `@ac`; verify they pass only with 1.2 and 2.2 in place
- [ ] 3.2 Keep the filtering in `scan_tags` so every check gets the filtered tags (REQ-SPECS-003) tagged `@req REQ-SPECS-003`; verify the 3.1 tests pass

## 4. Mark this repository's samples and document the markers

- [ ] 4.1 Add `# specworks: ignore-tags` next to every sample tag in `tests/*.py`, a block around the samples in `tests/test_walkthrough.py`, and a block around the `trace.py` docstring's examples (REQ-SPECS-001, REQ-SPECS-002); verify `specworks trace --change ignore-sample-tags` lists no unknown tags and `uv run pytest` passes
- [ ] 4.2 Document both markers in the `trace.py` module docstring (REQ-SPECS-001, REQ-SPECS-002); verify that the docstring's quoted markers open no block (AC-SPECS-002.3) and lint passes
