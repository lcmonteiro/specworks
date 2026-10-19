# Review: unique-capability-paths

Base: `origin/main`

## Findings

- [ ] R1 **quality** `capability add` checks the raw `--path`, but the config stores it normalised (`validate_relative`: `\` -> `/`), so `--path 'src\auth'` passes the pre-check and is rolled back by the load check with the generic "add it by hand" message instead of naming `auth` (REQ-PROJ-016, AC-PROJ-016.4; `src/specworks/cli/project.py:254`)
  - **Decision**: back to code: normalise `--path` with `validate_relative` before computing the docs folder, and add a test with a backslash path (agreed with the user)
  - done in code: `capability add` normalises `--path` with `validate_relative` before the check; `test_capability_add_refuses_a_taken_path` also adds `src\\auth\\` and expects `already used by auth` (it fails without the fix)

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

The check at load (`_check_docs_folders`, next to `_check_prefixes`) and the
pre-check in `capability add` implement REQ-PROJ-016. The four tests check
each criterion through the CLI. Coverage is 98%. R1 goes back to code for the
path normalisation.
