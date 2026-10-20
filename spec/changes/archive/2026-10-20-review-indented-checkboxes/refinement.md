# Refinement: review-indented-checkboxes

## Problem

In review.md, a checkbox that isn't a finding is reported as unreadable only
when it starts at column 0. Indented under a bullet that isn't a finding, it is
ignored, so an open item can hide from the review gate and validate.
Reproduced: `- Follow-ups:` followed by `  - [ ] reset still ignores case`
gives no finding and no problem, while the same line at the top level is
reported. This was found as suspected bug 7 of `baseline-workflow`.

## Context

**Observed:**
- `workflow/review.py`, `parse_review`: `FINDING_RE` reads `- [ ] R<n> …` at
  any indentation. Another checkbox is reported only when
  `not line.startswith((" ", "\t"))` ("indented ones belong to a finding"). An
  indented checkbox with no finding above it (`current is None`) is neither
  read nor reported.
- Checkboxes under a finding (a sub-step under its Decision) are part of that
  finding and must stay allowed (`test_a_checkbox_inside_a_finding_is_part_of_it`).
- The "Changed files without tags" section is collected as text and not parsed
  for findings. Code fences and HTML comments are ignored.
- Living spec of `workflow`: REQ-FLOW-010 says "a top-level checkbox that is not
  a finding … SHALL be reported as unreadable", which matches the code. The gap
  is in the spec too.
- The review template and the instructions only use checkboxes for findings.

**Assumed:**
- Reviewers don't keep loose checklists in review.md: open work is a finding,
  done work is a ticked finding.

## Constraints

- [hard] No unticked checkbox can hide from the review gate and validate.
- [hard] Checkboxes inside a finding's block, the "Changed files without tags"
  section, code fences and comments behave as today.

## Options

### Option A: Report any checkbox outside a finding

A checkbox outside a finding's block, at the top level or indented, ticked or
not, is reported as unreadable.

- **Pros:** One rule, whatever the indentation. Closes the gap completely.
- **Cons:** A ticked note outside findings now fails too (a one-line edit).
- **Effort:** S
- **Touches:** `workflow`

### Option B: Report only unticked indented checkboxes

- **Pros:** Targets exactly the risk.
- **Cons:** Two rules for one kind of line.
- **Effort:** S
- **Touches:** `workflow`

### Option C: Keep it, and document it

- **Pros:** No code change.
- **Cons:** An open item can still hide.
- **Effort:** S
- **Touches:** `workflow`

## Recommendation

**Option A**, chosen with the user. The rule becomes "a checkbox outside a
finding is always reported", which is simple, and review.md has no use for
loose checklists.

## Open Questions

None.

## Candidate Capabilities

- `workflow`: REQ-FLOW-010 MODIFIED. Its description drops "top-level", and it
  gets a new criterion for an indented checkbox outside any finding.
