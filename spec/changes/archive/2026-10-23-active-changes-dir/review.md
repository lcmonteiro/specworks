# Review: active-changes-dir

Base: `origin/main`

## Findings

- [x] R1 **test-gap** 12 tests in `tests/test_diagrams.py` fail: the fixture's change folder is one level deeper (`spec/changes/active/<name>`), but the tests still take the project root as `change.parents[2]` (now `spec/`, not the root); REQ-PROJ-001, REQ-PROJ-020 (`tests/test_diagrams.py:78`, `:176`, `:192`, `:254`)
  - **Proposal**: back to test: use `change.parents[3]` at the four places (or compute the root once in the `change` fixture) and run `uv run pytest`
  - **Decision**: back to test: use `change.parents[3]` at the four places (or compute the root once in the `change` fixture) and run `uv run pytest`
  - done in test: the four places in `tests/test_diagrams.py` use `change.parents[3]`; `uv run pytest` passes (602 tests)
- [x] R2 **design-gap** `Config.archive_dir` is a new public property (`src/specworks/core/config.py`), used by `list_archived` for its error path, but design.md `## Interfaces` says "None" and lists only `changes_dir`, `changes_path` and `archive_path`
  - **Proposal**: back to design: list `Config.archive_dir -> str` (`<dir>/changes/archive`) under `## Interfaces`; the code and its callers already match
  - **Decision**: back to design: list `Config.archive_dir -> str` (`<dir>/changes/archive`) under `## Interfaces`; the code and its callers already match
  - done in design: design.md `## Interfaces` lists `Config.archive_dir -> str`, as in the code

## Changed files without tags

- `tests/helpers.py`: path-only update (`spec/changes/active/<ref>`) in a test helper, no behaviour of its own
- `tests/test_walkthrough.py`: path-only update of the `C` constant to `spec/changes/active/<ref>`; the walkthrough is not tied to a single criterion

## Summary

Cycle 2: R1 and R2 are done and closed. The suite passes (602 tests). Re-checked the code against the specs and design: every requirement has tagged code, every criterion has a test, the interfaces in design.md match `Config` (`changes_dir`, `changes_path`, `archive_dir`, `archive_path`), and no loose `spec/changes/<name>` path is left in `src`, `.github` or `spec.yml`. No new findings.
