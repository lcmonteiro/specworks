# Proposal: fix-route-quoted-forms

## Why

A finding's route (`back to <step>:`, `back to design only:`) and its
`done in <step>:` are read from anywhere in a line of its block, so a form
only quoted in its text sets them. It made R2 and R3 of
`skip-halves-for-design-text` design-only, so a build cycle would have
skipped the test and code halves with nobody deciding it (refinement.md,
option A).

## What Changes

- A route form counts only where it starts a line's text, after the line's
  indentation, an optional bullet and an optional bold label such as
  `**Decision**:` or `**Proposal**:`. Anything after it on the line, and the
  finding's own line (`- [ ] R<n> ...`), is text.
- `done in <step>:` is read by the same rule, so a `confirmed in review:` or
  any other line that quotes it no longer sets the step a finding was done in.
- `specworks finding add`, `decide` and `done` route by the same rule: a
  finding whose text or Proposal only quotes a form is routed by its type, or
  by the form its Proposal starts with.
- **BREAKING** (workflow): a route written mid-line, or on the finding's own
  line, no longer routes. No archived review writes one: re-read with the new
  rule, only R2 and R3 of `skip-halves-for-design-text` change, to the route
  their Decision gives.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `workflow`: REQ-FLOW-010 Reading review.md (where a route form and
  `done in` count), REQ-FLOW-016 Writing findings to review.md (a finding that
  quotes a form is added and routed by that rule).

## Related requirements

Found with `specworks spec find "back to" "done in" "design only" "finding add" "finding decide" "finding done"`:

- REQ-FLOW-010 modified
- REQ-FLOW-016 modified
- REQ-FLOW-012 left: build cycles start from each finding's step as REQ-FLOW-010 reads it; the rule for the steps is unchanged
- REQ-CLI-011 left: `finding` prints the finding as `cycle` reads it, which follows REQ-FLOW-010
- REQ-PROJ-006 left: "leads back to an ancestor" is about module links, not findings
- REQ-CLI-007 left: "the phases to go back to" is about close, not findings

## Impact

- `src/specworks/workflow/review.py`: how `parse_review` and `add_finding`
  find a route and a `done in` in a line.
- Tests in `tests/test_review_phase.py` and `tests/test_findings.py`.
- No CLI, template or skill change: they already write each form at the start
  of its line.

## Out of Scope

- Which line wins when a finding's block has more than one route (the last
  one still does).
- Refusing a finding's text that quotes a form.
- Narrower `spec find` matching; the wiki.
