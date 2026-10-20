# Review: diagrams-dir-root

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

`diagrams --dir` resolves a relative folder from the workspace root and refuses
one that doesn't exist (AC-CLI-008.6, AC-CLI-008.7); its help text says so.
Checked by hand from `src/specworks/workflow/`: `--dir src/specworks/core/docs`
finds the folder, `--dir src/nope` fails naming it. The close skill's
`specworks diagrams --dir "<docsPath>"` needs no change. No findings.
