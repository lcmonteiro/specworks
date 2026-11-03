# Refinement: test-folders-per-capability

## Problem

`capability-tests` taught the review gate to run only the tests of the
capabilities a change touches, but this repo still keeps its 25 test files
flat in `tests/` and sets no `commands.test_scoped`, so its own review gate
still runs the whole suite. Most files mix the tests of two to five
capabilities, so no file maps to one capability as it is. That change left
the move for later (its Out of Scope).

## Outcomes

- `specworks context` shows `tests/<capability>/` for every capability, and
  each folder holds only that capability's tests.
- The review gate of a change runs only the touched capabilities' folders
  (`uv run pytest tests/<capability> ...`); validate still runs everything.
- The suite keeps exactly the same tests: the same test IDs collected, all
  passing, coverage unchanged.

## Context

**Observed:**
- `tests/` holds 25 `test_*.py` files plus `conftest.py`, `helpers.py` and
  `samples.py`; tests import them flat (`from helpers import ...`), which
  works because pytest puts `tests/` on `sys.path` (rootdir import mode).
- Every tagged test function carries the tags of one capability first
  (`# @ac AC-<prefix>-...`); 11 tests also tag a second capability. Only 7
  files hold one capability's tests; the others share file-local helpers and
  fixtures between capabilities.
- Untagged tests: skill wording (80 in `test_skills.py`), the walkthrough,
  and a few per file.
- `tests_dir` defaults to `tests`, so the folders are `tests/project`,
  `tests/specs`, `tests/workflow`, `tests/integrations` and `tests/cli`.
- `test_globs: ["tests/**/*.py"]` already reaches subfolders.

**Assumed:**
- Splitting a file by test keeps behaviour, since each test only depends on
  its fixtures and helpers.

## Constraints

- [hard] No behaviour change: no code in `src/` changes; the change is `skip-specs`.
- [hard] No test lost, duplicated or changed; tags unchanged.
- [soft] No duplicated helper code between the split files.

## Options

### Option A: split each file by test

Each tagged test goes to `tests/<capability>/test_<topic>.py` for its first
tag's capability; untagged tests stay in `tests/test_<topic>.py`. Helpers and
fixtures shared by the parts move to `tests/support/<topic>.py` (fixtures as
plain `make_<name>` functions behind a one-line fixture in each part).
pytest runs in `importlib` import mode with `pythonpath = ["tests"]`, since
file names repeat across folders.

- **Pros:** each folder holds exactly its capability's tests, so scoped runs
  are precise.
- **Cons:** more files (about 60); a test tagging two capabilities runs only
  with the first one's folder.
- **Effort:** M
- **Touches:** none (tests and config only)
- **Outcomes:** meets all.

### Option B: move whole files by their main capability

- **Pros:** small, keeps file history.
- **Cons:** most folders would hold other capabilities' tests, so a scoped
  run misses tests of the touched capability that sit elsewhere.
- **Effort:** S
- **Touches:** none
- **Outcomes:** fails the first.

## Recommendation

Option A, agreed with the user: split by test, untagged tests stay in
`tests/`, and `commands.test_scoped: uv run pytest {paths}`.

## Open Questions

None.

## Candidate Capabilities

- None: tests, pytest settings and the project config only; `skip-specs`.
