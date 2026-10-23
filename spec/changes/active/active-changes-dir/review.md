# Review: active-changes-dir

Base: `origin/main`

## Findings

- [ ] R1 **test-gap** 12 tests in `tests/test_diagrams.py` fail: the fixture's change folder is one level deeper (`spec/changes/active/<name>`), but the tests still take the project root as `change.parents[2]` (now `spec/`, not the root); REQ-PROJ-001, REQ-PROJ-020 (`tests/test_diagrams.py:78`, `:176`, `:192`, `:254`)
  - **Proposal**: back to test: use `change.parents[3]` at the four places (or compute the root once in the `change` fixture) and run `uv run pytest`
- [ ] R2 **design-gap** `Config.archive_dir` is a new public property (`src/specworks/core/config.py`), used by `list_archived` for its error path, but design.md `## Interfaces` says "None" and lists only `changes_dir`, `changes_path` and `archive_path`
  - **Proposal**: back to design: list `Config.archive_dir -> str` (`<dir>/changes/archive`) under `## Interfaces`; the code and its callers already match

## Changed files without tags

- `tests/helpers.py`: path-only update (`spec/changes/active/<ref>`) in a test helper, no behaviour of its own
- `tests/test_walkthrough.py`: path-only update of the `C` constant to `spec/changes/active/<ref>`; the walkthrough is not tied to a single criterion

## Summary

Code, specs and design agree: every requirement has tagged code, every criterion has a test that asserts its THEN, and no `spec/changes/<name>` path is left in `src`, `.github` or `spec.yml`. The suite has 12 failures, all from R1 (tests still at the old folder depth); R2 is an interface the design does not list. Both are proposed back to the owning phase, nothing was fixed here.
