# Design: skip-halves-for-design-text

## Context

See `proposal.md`. Routing lives in `src/specworks/workflow/review.py`:
`BACK_RE` reads `back to <step>:` anywhere in a finding's block, `DONE_RE`
reads `done in <step>:`, `NEXT_STEP` gives the step after a done one, and
`DECISION_RE` checks the form `finding decide` writes. `next_cycle` in
`src/specworks/workflow/cycle.py` turns the open findings' steps into the
cycle.

## Goals / Non-Goals

**Goals:**
- `back to design only:` is read, written and planned as design → review.
- Every review.md written today reads exactly as before.

**Non-Goals:**
- `only` for any step but design.

## Decisions

### `only` is read with the `back to` that carries it (REQ-FLOW-010)

`BACK_RE` becomes
`\bback to (?P<phase>specify|design|implement|test|code)(?P<only>\s+only)?\s*:`.
A match with `only` sets the finding's `design_only` when the step is design;
`only` after any other step is not a route, so the finding stays unrouted
unless something else routes it (and the gate reports it as today). The last
`back to` in the block wins, as today, so a later plain `back to design:`
clears `design_only`.

### The step after design (REQ-FLOW-010)

After `done in design:`, a `design_only` finding goes to review; any other to
implement (`NEXT_STEP`). Kept as one small rule next to `NEXT_STEP` rather
than a second table.

### Which halves join design (REQ-FLOW-012)

In `next_cycle`, a finding needs both halves when its step is implement, or
when its step is design and it is not `design_only`. The halves are then both
halves, or the ones findings name; design-only findings add none. The start
stays: design when design is in the cycle, implement when a half is, review
otherwise.

### The Decision form (REQ-FLOW-016)

`DECISION_RE` accepts `back to design only:`; `DECISION_FORM` names it:
`a decision starts with 'back to <step>:' (specify, design, implement, test
or code), 'back to design only:' or 'accepted:'`. `back to code only:` (and
the other steps with `only`) fails that check, so it is refused before any
write.

### Pinned wording

The test half asserts these and the code half writes them, verbatim:
- `DECISION_FORM`:
  `a decision starts with 'back to <step>:' (specify, design, implement, test or code), 'back to design only:' or 'accepted:'`.
- `/specworks-review` step for proposals:
  `back to design only:` with `when the design fix needs no test or code change`.
- `/specworks-build` cycle rules: `` `back to design only:` → design, review ``.

## Interfaces

Agreed with the user

- `src/specworks/workflow/review.py`: `Finding.design_only: bool = False`
  (REQ-FLOW-010); `Finding.to_dict()` adds `"designOnly": true` when set, so
  `specworks cycle --json` and `specworks finding ... --json` show it
  (REQ-FLOW-012, REQ-FLOW-016).
- No new command, option or function.

## Diagrams

No structural change.

## Risks / Trade-offs

- [a design-only fix turns out to need code] -> the next review finds the gap
  and routes it as usual; the cost is one review, not a wasted cycle.
- [`only` written after another step] -> refused by `finding decide`, and
  unrouted (reported by the gate) when hand-written.

## Open Questions

None.
