# Review: baseline-cli

Base: `origin/main`

## Findings

None.

A baseline changes no behaviour. In `src/specworks/cli` this change adds only
`# @req REQ-CLI-…` comment lines, on `main`, `_reporting_errors`, `fail`,
`workspace`, `resolve_change`, `resolve_archived` and the commands that decide
each behaviour (`init`, `context`, `list`, `module add`/`list`,
`capability add`, `status`, `new`, `phase`, `abandon`, `skip-specs`, `close`,
`diagrams`). In the tests it adds only `# @ac AC-CLI-…` comments (appended to
existing tag lines where a test already carried one), plus two new tests, both
passing against the current code:
- `tests/test_modules.py::test_module_add_refuses_a_folder_outside_the_project`
  (AC-CLI-005.3)
- `tests/test_diagrams.py::test_diagrams_refuses_a_folder_outside_the_workspace`
  (AC-CLI-008.5)

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the earlier baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

The existing behaviour of `cli` is recorded as REQ-CLI-001..008 (36 criteria).
The existing tests are tagged, two tests were added, and the code is tagged. No
drift was found. The suspected bugs stay out of scope (see proposal.md):
`module add` can link a folder another module owns, `run <unknown key>` gives a
misleading hint, and `diagrams --dir` is relative to the working directory.
