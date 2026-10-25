# Review: module-outside-workspace

Base: `origin/main`

## Findings

None.

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

`_load_tree` refuses a module whose resolved folder is outside the top level's,
before reading its config (AC-PROJ-006.9, with and without a config there).
`_check_nesting` lost its skip, and the cycle check its outside-the-root
fallback, both unreachable now; the test of the skip was removed. Checked by
hand: the reproduction from refinement.md now prints the error instead of
crashing. The living design's note that such a module "is not checked" is
updated at close. No findings.
