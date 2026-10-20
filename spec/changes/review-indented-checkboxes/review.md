# Review: review-indented-checkboxes

Base: `origin/main`

## Findings

None.

Checked against REQ-FLOW-010 (MODIFIED):
- AC-FLOW-010.5: `parse_review` reports a checkbox that isn't a finding unless
  it is indented inside an open finding's block (`current is not None`). A new
  section or a top-level line still ends a finding's block, so a loose checkbox
  after it is reported. The parser test checks both sides (a loose indented
  checkbox is reported, the same line under a finding is not). The gate test
  shows the review gate failing with `--allow-open`, since the readability
  check blocks. Both failed before the fix.
- AC-FLOW-010.1 to .4 still pass, including
  `test_a_checkbox_inside_a_finding_is_part_of_it`. All 46 tests in
  `tests/test_build_cycle.py` and `tests/test_review_phase.py` pass, and so do
  the full suite and lint.

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

A checkbox outside a finding is now always reported, so open work can't hide
in review.md behind indentation. No drift.
