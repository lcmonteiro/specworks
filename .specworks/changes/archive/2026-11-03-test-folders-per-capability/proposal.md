# Proposal: test-folders-per-capability

## Why

This repo's review gate still runs the whole suite on every build cycle:
its tests sit flat in `tests/` and it sets no `commands.test_scoped`, so the
scoped run added by `capability-tests` never applies here. The refinement
chose Option A: split the test files by test into one folder per capability.

## What Changes

- Every tagged test moves to `tests/<capability>/test_<topic>.py`, the
  capability of its first `@ac` tag (`project`, `specs`, `workflow`,
  `integrations`, `cli`); a file holding one capability's tests moves whole
  (`git mv`).
- Untagged tests (skill wording, the walkthrough, a few per file) stay in
  `tests/test_<topic>.py`.
- Helpers and fixtures used by the tests of more than one capability move to
  `tests/support/<topic>.py`; a shared fixture becomes a plain
  `make_<name>` function there, with a one-line fixture of the same name in
  each part that uses it. `conftest.py`, `helpers.py` and `samples.py` stay.
- `pyproject.toml`: pytest runs with `--import-mode=importlib` and
  `pythonpath = ["tests"]`, since file names now repeat across folders.
- `.specworks/config.yml`: `commands.test_scoped: uv run pytest {paths}`,
  and the context text names the new layout; `CLAUDE.md`'s layout table too.

## Capabilities

None: tests, pytest settings, the project config and `CLAUDE.md` only; no
code in `src/` changes. The change is marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Related requirements

- REQ-PROJ-027 left: `tests_dir` keeps its default `tests`, which gives the new folders.
- REQ-PROJ-028 left: `test_scoped` holds `{paths}`, as it requires.
- REQ-FLOW-017 left: the review gate's scoped run is used as specified.
- REQ-SPECS-011 left: `test_globs: ["tests/**/*.py"]` already scans the subfolders.

## Impact

- `tests/` (about 60 files: 5 capability folders, `support/`, the untagged
  remainders), `pyproject.toml`, `.specworks/config.yml`, `CLAUDE.md`.
- No CLI, API or data change. The collected test IDs stay the same
  (only their paths change).

## Out of Scope

- Splitting a test that tags two capabilities (11 tests): it runs with its
  first tag's folder, and validate still runs it with the full suite.
- Renaming, rewriting or retagging any test.
- Tagging the untagged tests.
