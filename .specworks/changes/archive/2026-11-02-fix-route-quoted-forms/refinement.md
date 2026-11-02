# Refinement: fix-route-quoted-forms

## Problem

A finding in review.md is routed by any `back to <step>:` (or
`back to design only:`) and its `done in <step>:` by any `done in <step>:`,
found anywhere in a line of its block. So a form only quoted in a finding's
text, Proposal, Decision or `confirmed in review:` line sets its route. In
`skip-halves-for-design-text` this made R2 and R3 design-only, so a build
cycle would skip the test and code halves with nobody deciding it, and
`finding add` refused a proposal that quoted a form.

## Outcomes

- A route form quoted in a finding's text (its own line, a Proposal, a
  Decision, a `done in` or `confirmed in review:` line) no longer changes
  where the finding goes, nor the step it was done in.
- Every route written the usual way (`finding add`, `finding decide`,
  `finding done`, the review template) routes as today: re-reading the
  archived reviews changes only R2 and R3 of `skip-halves-for-design-text`.
- `finding add` accepts a proposal that quotes a route form.

## Context

**Observed:**
- `src/specworks/workflow/review.py`: `BACK_RE` and `DONE_RE` are searched
  anywhere in a line; `_route` takes the first `back to` in a line, and in
  `parse_review` the last line of the block with one wins. `add_finding`
  checks the route of its text and proposal lines; `decide_finding` routes
  from the decision (which `DECISION_RE` already anchors at its start).
- `workflow` (REQ-FLOW-010 Reading review.md, REQ-FLOW-016 Writing findings),
  living docs in `src/specworks/workflow/docs/`. REQ-FLOW-010 says a finding
  is routed by "a `back to <step>:` in its own block".
- In every archived review.md, real routes start their line: 54 Decisions and
  Proposals start with `back to <step>:`, every `done in` starts its own
  bullet, and no finding line carries one. Only R2 and R3 of
  `skip-halves-for-design-text` quote a form mid-line.
- A rough version of option A, run over all archived reviews, changes only
  those two findings (R3 then goes to implement, not review).
- No test writes a route on a finding's own line or mid-line.

**Assumed:**
- Hand-written reviews also put the route at the start of a sub-bullet, as
  the template and the skills show.

## Constraints

- [hard] Routes written by the finding commands and the template keep their
  meaning; IDs are never renumbered.
- [hard] Deterministic: the route depends only on where the form stands in
  the line, never on guessing intent.
- [soft] Keep the change in `review.py` small; no new syntax for the user.

## Options

### Option A: only at the start of a line

A `back to <step>:`, `back to design only:` or `done in <step>:` counts only
where it starts a line's text, after the bullet and an optional bold label
(`**Decision**:`, `**Proposal**:`). The rest of a line, and the finding's own
line, are text.

- **Pros:** simple and deterministic; matches how every route is written today.
- **Cons:** rewords REQ-FLOW-010; a route written mid-line by hand stops routing.
- **Effort:** S
- **Touches:** `workflow`
- **Outcomes:** meets all three.

### Option B: ignore text in quotes or backticks

Strip quoted and backticked spans before looking for a form.

- **Pros:** smallest change to the rule.
- **Cons:** a form mentioned without quote marks still routes; apostrophes
  in prose make quote pairs unreliable.
- **Effort:** S
- **Touches:** `workflow`
- **Outcomes:** meets the second; the first and third only when quoted.

### Option C: route only from the Decision

Read `back to` only from the `**Decision**:` line (and `done in` from its own line).

- **Pros:** strictest.
- **Cons:** 28 archived Proposals routed their finding before a Decision, and
  `finding add` routes from the Proposal; those findings would lose their route.
- **Effort:** S
- **Touches:** `workflow`
- **Outcomes:** meets the first and third; fails the second.

## Recommendation

Option A, agreed with the user: it meets all three outcomes, and the archive
check shows only the two misread findings change.

## Open Questions

- None. Out of scope: which line wins when a finding has more than one route
  (the last one still does), narrower `spec find` matching, the wiki.

## Candidate Capabilities

- `workflow`: modified - REQ-FLOW-010 (where a route form counts) and
  REQ-FLOW-016 (`finding add`/`decide`/`done` read routes by the same rule).
