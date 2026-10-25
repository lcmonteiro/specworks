# Review: baseline-project

Base: `origin/main`

## Findings

None.

A baseline changes no behaviour. In `src/specworks/core` the diff against the
base adds only `# @req REQ-PROJ-…` comment lines. In the tests it adds only
`# @ac AC-PROJ-…` comment lines, plus one new test,
`tests/test_modules.py::test_a_module_inherits_the_commands_it_does_not_set`
(AC-PROJ-007.2). That test passes against the current code. Each tag sits on the
function that decides its behaviour (e.g. REQ-PROJ-005 on
`workspace._check_prefixes`, REQ-PROJ-014 on `runner.cached_run` and
`tree_fingerprint`), and each `@ac` test asserts its criterion's THEN.

## Changed files without tags

The base `origin/main` also lacks the closed change `ignore-sample-tags`, which
is on this branch. These files carry only its `specworks: ignore-tags` markers,
recorded in its archive (`spec/changes/archive/2026-10-19-ignore-sample-tags/`):

- `tests/helpers.py`: ignore-sample-tags markers only.
- `tests/test_design_phase.py`: ignore-sample-tags markers only.
- `tests/test_review_phase.py`: ignore-sample-tags markers only.
- `tests/test_specified.py`: ignore-sample-tags markers only.
- `tests/test_test_phase.py`: ignore-sample-tags markers only.
- `tests/test_walkthrough.py`: ignore-sample-tags ignore block only.

## Summary

The existing behaviour of `project` is recorded as REQ-PROJ-001..015 (49
criteria). The existing tests are tagged, one test was added (AC-PROJ-007.2),
and the code is tagged. No code, spec or design drift was found. The suspected
bugs stay out of scope, as candidates for their own changes (see proposal.md):
a code path shared by two capabilities, the config marker documented as the
"first line" but matched on any line, run reuse crashing on an unreadable
untracked file, and a module path that loops back through a symlink.
