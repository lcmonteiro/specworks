# Review: test-folders-per-capability

Base: `origin/main`

## Findings

None.

Checked against the diff: the collected test IDs (without their folder) are
the same 943 as on `origin/main`; each capability folder holds only its own
prefix's `@ac` tags (other prefixes there are sample-project IDs inside
strings: AUTH, AUHT, AUDIT, OTHER); no file in `src/` changed; lint, typecheck
and the full suite pass, with branch coverage above 95%.

## Changed files without tags

- `tests/support/archive.py`, `tests/support/capability_tests.py`,
  `tests/support/cli.py`, `tests/support/close_phase.py`,
  `tests/support/code_phase.py`, `tests/support/commit.py`,
  `tests/support/config_set.py`, `tests/support/design_phase.py`,
  `tests/support/diagrams.py`, `tests/support/find_requirements.py`,
  `tests/support/findings.py`, `tests/support/merge.py`,
  `tests/support/modules.py`, `tests/support/propose.py`,
  `tests/support/run_cache.py`, `tests/support/skills.py`: helpers and
  fixtures shared by the parts of one split file; helpers carry no tags
  (design.md "Shared helpers in `tests/support/<topic>.py`").
- `tests/test_archive.py`, `tests/test_cli.py`, `tests/test_close_phase.py`,
  `tests/test_code_phase.py`, `tests/test_design_phase.py`,
  `tests/test_diagrams.py`, `tests/test_modules.py`, `tests/test_propose.py`,
  `tests/test_run_cache.py`, `tests/test_skills.py`, `tests/test_test_phase.py`:
  the untagged tests left in `tests/` by the split, unchanged.
- `tests/test_capability_tests.py` (deleted): split whole into
  `tests/project/` and `tests/workflow/`.
- `pyproject.toml`, `.specworks/config.yml`, `CLAUDE.md`: pytest settings,
  `commands.test_scoped` and the layout text (tasks 1.2, 2.1, 2.2).
