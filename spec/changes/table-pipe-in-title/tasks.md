# Tasks: table-pipe-in-title

## 1. Escape `|` in generated tables

- [x] 1.1 Add `table_cell(text)` to `specfile.py` as a stub that returns `text` unchanged (REQ-SPECS-012, REQ-SPECS-013); verify it builds and the existing tests pass
- [x] 1.2 Write failing tests for AC-SPECS-012.5 (`tests/test_propose.py`, a traced title with `|`) and AC-SPECS-013.6 (`tests/test_close_phase.py`, an index row with `|`), tagged `@ac`; verify they fail because the row has an extra cell
- [ ] 1.3 Implement `table_cell` and use it for every title in `requirements_index` and `to_markdown` (REQ-SPECS-012, REQ-SPECS-013) tagged `@req`; verify the 1.2 tests and the existing AC-SPECS-012.x and 013.x tests pass
