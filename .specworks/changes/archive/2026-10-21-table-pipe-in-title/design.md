# Design: table-pipe-in-title

## Decisions

### One helper for every generated table cell

`table_cell(text)` in `specfile.py`, which both `merge.py` and `trace.py`
already import, returns the text with `|` escaped as `\|`. `requirements_index`
and `to_markdown` pass every title through it; IDs, paths and task numbers
can't hold `|` and are left alone. Serves: REQ-SPECS-012, REQ-SPECS-013.

## Interfaces

- `src/specworks/specs/specfile.py`: `table_cell(text: str) -> str`, `text` with
  each `|` escaped for a markdown table cell.
