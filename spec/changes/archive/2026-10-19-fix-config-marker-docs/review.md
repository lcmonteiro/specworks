# Review: fix-config-marker-docs

Base: `origin/main`

## Findings

None.

The only change to the code is the module docstring of
`src/specworks/core/config.py`. It now says what `MARKER_RE` does (an
unindented `specworks: <n>` line, anywhere in the file) and what REQ-PROJ-001
states. No behaviour changed, so there are no delta specs (skip-specs), and the
full suite and lint pass.

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

The docstring now matches the code and the living spec. No drift.
