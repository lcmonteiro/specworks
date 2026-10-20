# Proposal: review-indented-checkboxes

## Why

In review.md, a checkbox indented under a bullet that isn't a finding is
ignored, so an open item can hide from the review gate and validate
(reproduced; suspected bug 7 of `baseline-workflow`; refinement.md, option A).

## What Changes

- Any checkbox outside a finding's block, at the top level or indented, ticked
  or not, is reported as unreadable. That fails the review gate (also with
  `--allow-open`) and validate.
- Unchanged: checkboxes inside a finding's block (its sub-steps), the "Changed
  files without tags" section, code fences and HTML comments.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workflow`: REQ-FLOW-010 "Reading review.md" MODIFIED. Its description says
  "a checkbox outside a finding" instead of "a top-level checkbox that is not a
  finding", and it gets a new criterion, AC-FLOW-010.5.

## Impact

`src/specworks/workflow/review.py` (`parse_review`) and
`tests/test_build_cycle.py`. No API, data or dependency change.

## Out of Scope

- Checkboxes in other workflow files (tasks.md has its own parser).
- The other suspected bugs.
