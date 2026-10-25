# Review: module-cycle-detection

Base: `origin/main`

## Findings

None.

Checked against REQ-PROJ-006 (MODIFIED) and its new criteria:
- AC-PROJ-006.6: `_load_tree` records each module's resolved folder before
  loading its children. A child whose folder is already recorded fails before
  its config is read, so a symlink back to an ancestor ends in a `ConfigError`,
  not a `RecursionError`. On the repro project the message is
  `module 'loop' (.) is the same folder as (top); a folder can be only one module, so remove one of the links`.
- AC-PROJ-006.7: the same record catches one folder linked by two parents. The
  test links `services/billing` again as `other` and expects both names. Before
  the fix, that workspace failed only by accident, on its capability's docs
  folder (REQ-PROJ-016), and without a capability it would have loaded twice.
- Before the fix, .6 failed with the crash and .7 with the wrong error. After
  it, all 39 tests in `tests/test_modules.py` pass, including AC-PROJ-006.1 to
  .5, and so do the full suite and lint.
- The folder is printed relative to the workspace root, like other messages.
  Its absolute fallback (a module folder outside the workspace, linked twice)
  has no test. It is the same expression the docs-folder check uses, so it is
  accepted as is.

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

A folder is now at most one module: a cycle through a symlink or a folder
linked twice fails with a clear error naming both. No drift.
