# Review: baseline-workflow

Base: `origin/main`

## Findings

None.

A baseline changes no behaviour. In `src/specworks/workflow` this change adds
only `# @req REQ-FLOW-…` comment lines. In the tests it adds only
`# @ac AC-FLOW-…` comment lines, plus one new test,
`tests/test_cli.py::test_instructions_for_an_unknown_artifact_are_refused`
(AC-FLOW-002.4), which passes against the current code. Each `@req` sits on the
function that decides the behaviour. `GATE_CHECKS` carries the tags of the gates
it defines (REQ-FLOW-004, 006, 007, 008, 011), and `validate_change` carries
REQ-FLOW-013 and the fix names `start` shows (REQ-FLOW-014).

## Changed files without tags

The base `origin/main` also lacks the closed changes `ignore-sample-tags` and
`baseline-project`, which are on this branch:

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags (archived at
  `spec/changes/archive/2026-10-19-ignore-sample-tags/`).
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

The existing behaviour of `workflow` is recorded as REQ-FLOW-001..014 (64
criteria). The existing tests are tagged, one test was added (AC-FLOW-002.4),
and the code is tagged. No drift was found. The suspected bugs stay out of scope
(see proposal.md): deleted files are not among the changed files, an
Interfaces file is also accepted at the workspace root, and an indented
non-finding checkbox in review.md is ignored silently.
