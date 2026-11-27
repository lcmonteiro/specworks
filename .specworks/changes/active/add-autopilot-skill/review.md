# Review: add-autopilot-skill

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **quality** The test `test_only_build_and_done_run_their_phases_in_subagents` and its comment ("A phase run by build or done") still say only build and done are coordinators, while it now asserts autopilot is one too (AC-HARNESS-004.3, task 2.1) (`tests/test_skills.py:46`)
  - **Proposal**: back to test: rename it to test_only_the_coordinators_run_their_phases_in_subagents and make its comment name build, done and autopilot; the assertions stay as they are
  - **Decision**: back to test: rename it to test_only_the_coordinators_run_their_phases_in_subagents and name build, done and autopilot in its comment

## Changed files without tags

- `tests/test_skills.py`: wording checks of the skill text (autopilot, refine, onboard); the skills have no capability yet, so these tests are untagged by the project's rule (CLAUDE.md), as task 2.1 and 3.1 say. Its stale test name is R1.

## Summary

The suite passes (1404 tests) and every requirement, criterion and tag lines up: `AutopilotPeer` gets `MERGE_RULE` like `BuildPeer` (REQ-HARNESS-004), the skill, refine and onboard carry the pinned wording of design.md, and the installed copies are fresh. One small finding, R1: a test's name and comment still say only build and done coordinate. Proposed back to test; no spec, design or code change.
