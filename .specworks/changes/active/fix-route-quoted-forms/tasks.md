# Tasks: fix-route-quoted-forms

## 1. Reading a route at the start of a line

- [x] 1.1 Confirm no stub is needed: the change touches only private helpers in `src/specworks/workflow/review.py` (design.md Interfaces: None) (REQ-FLOW-010); verify `specworks run lint` passes and the existing tests pass
- [ ] 1.2 [test] Write failing tests for AC-FLOW-010.9 in `tests/test_review_phase.py`, tagged `@ac AC-FLOW-010.9`: the finding that quotes `'back to design only:'` on its own line, starts its Proposal with `back to code:` and quotes `done in test:` under `confirmed in review:` is routed to code, not design-only, with no `done in` step; the same finding with no Proposal is routed to code by its type; verify they fail for the right reason
- [x] 1.3 [code] Read `back to <step>:`, `back to design only:` and `done in <step>:` only where they start a line's text (after indentation, an optional bullet and an optional bold label), never on the finding's own line, in `parse_review` (REQ-FLOW-010), tagged `@req REQ-FLOW-010`; verify with lint and `specworks cycle` on a sample review.md that quotes a form

## 2. Writing a finding that quotes a form

- [ ] 2.1 [test] Write failing tests for AC-FLOW-016.8 in `tests/test_findings.py`, tagged `@ac AC-FLOW-016.8`: a `quality` finding whose text and proposal only quote forms is added and routed to code, not design-only; one whose proposal starts with `back to test:` and quotes `done in code:` is routed to test; verify they fail for the right reason
- [x] 2.2 [code] Make `add_finding` and `decide_finding` expect the route by the same line-start rule (the Proposal or Decision line only, else the type) (REQ-FLOW-016), tagged `@req REQ-FLOW-016`; verify with lint and `specworks finding add` on a sample change with a quoted form
