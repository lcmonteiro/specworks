# Review: module-interface-paths

Base: `origin/main`

## Findings

None.

Checked against REQ-FLOW-006 (MODIFIED):
- AC-FLOW-006.6: `interface_files_exist` counts a named path only when, read
  relative to the module folder or the workspace root, it resolves to an
  existing file inside the module folder. The test adds module `billing`,
  names `src/invoices.py` while only the top level has it (the gate lists it),
  then creates the module's file and passes with both the module-relative and
  the workspace-relative form. It failed before the fix. On the refinement's
  repro project the check now fails, listing `src/invoices.py`.
- Top-level changes are unchanged (their module folder is the workspace root).
  All 18 tests in `tests/test_design_phase.py` pass, including AC-FLOW-006.1 to
  .5, and so do the full suite and lint.
- A consequence, as the spec now states: in a module's change, a path that
  leaves the module (`../shared/x.py`) no longer counts. Work across modules
  belongs to a change at the top level or in the lowest common module.

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

A module's change now needs its Interfaces files in its own folder, named
either way. No drift.
