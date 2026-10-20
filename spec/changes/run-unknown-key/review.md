# Review: run-unknown-key

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

`run_command` refuses a key that is not a command key, listing the valid ones,
and the unconfigured message's example names the key asked for
(AC-PROJ-013.3, AC-PROJ-013.4). Checked by hand: `run frobnicate` and
`run build` print the new messages. The gates only ask for valid keys, so they
are unaffected. No findings.
