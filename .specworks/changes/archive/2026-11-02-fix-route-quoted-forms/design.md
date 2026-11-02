# Design: fix-route-quoted-forms

## Context

`src/specworks/workflow/review.py` finds routes with `BACK_RE.finditer` and
`DONE_RE.search` anywhere in a line; `_route(line)` serves `parse_review`,
`add_finding` and `decide_finding`. See proposal.md for why.

## Goals / Non-Goals

**Goals:**
- One rule, in one place, for where a form starts a line, used by both
  `back to` and `done in` and by every reader and writer of findings.

**Non-Goals:**
- Changing which line wins in a block, or the forms themselves.

## Decisions

### Where a line's text starts

A line's text starts after, in order: its indentation; an optional bullet
(`-`, `*`, `+`, `1.` or `1)`) and the spaces after it; an optional bold
label of words and an optional colon, bold before or after the colon
(`**Decision**:`, `**Decision:**`, `**Proposal**:`), and the spaces after it.
The form must start right there; `BACK_RE` and `DONE_RE` are matched at that
position (`match`, not `search`). Any bold label is accepted, not only
Decision and Proposal: a hand-written `**Fix**: back to code:` keeps routing,
and the rule stays one pattern. Serves: REQ-FLOW-010.

Alternatives: only `Decision`/`Proposal` labels (would break hand-written
labels for no gain); a fixed list of line kinds (`done in` has no label, so
two rules).

### The finding's own line is text

`parse_review` reads routes only from the lines after a finding's checkbox
line, so `- [ ] R1 back to code: x` is not routed (its text starts with the
ID, which never matches). `add_finding` reads the route from its Proposal
line only, by the same rule. Serves: REQ-FLOW-010, REQ-FLOW-016.

### `decide_finding`

The decision text is already anchored by `DECISION_RE`; its route is read by
the same line-start rule applied to the Decision line it writes, so what it
expects is what `parse_review` reads. Serves: REQ-FLOW-016.

## Interfaces

None: only private helpers in `src/specworks/workflow/review.py` change
(`_route(line)` reads the form at the line's start; a private
`_done_in(line)` does the same for `done in`). `Finding`, `parse_review`,
`add_finding`, `decide_finding` and `mark_finding_done` keep their signatures.

## Diagrams

No structural change.

## Risks / Trade-offs

- [a route written mid-line by hand stops routing] -> the finding then routes
  by its type, or is reported as unreadable when it has none, so it is never
  silently skipped; no archived review has one.

## Open Questions

None.
