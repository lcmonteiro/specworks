# Refinement: skip-halves-for-design-text

## Problem

A review finding whose agreed fix touches only design.md (no API, no test,
no code) still runs a full build cycle: design, then both implement halves
(a git worktree, two subagents), then review. The halves find nothing to do
and commit only the phase marker. It happened in
`specify-related-requirements` (cycle 3, finding R2, whose Decision already
said "no code or test change"), and it costs the user a cycle's time for no
work.

## Outcomes

- A design finding whose Decision says `back to design only: ...` runs
  design → review, with no test or code half and no worktree.
- The cycle question at the end of review already shows the shorter cycle
  (`Start cycle 2: design → review?`), so the user agrees to what will run.
- A design finding without `only` runs design → test | code → review, as
  today.

## Context

**Observed:**
- `src/specworks/workflow/cycle.py` `next_cycle` (REQ-FLOW-012): a finding
  needing design adds design and both halves, then review.
- `src/specworks/workflow/review.py`: `BACK_RE` reads `back to <step>:`,
  `DONE_RE` reads `done in <step>:`, and `NEXT_STEP` sends a finding done in
  design to implement, always. `DECISION_RE`/`DECISION_FORM` check a
  Decision's form for `specworks finding decide` (REQ-FLOW-016) and the
  review gate.
- The `specify-related-requirements` archive: R2's two implement commits
  (`5ac0614`, `1cdbddf`) hold only `.change.yaml` and review.md.
- Counterexample to detecting it: in `add-onboarding-skill`, R1 was a
  design-gap whose design step changed only design.md, yet the skill text
  (code) still had to follow.
- The build skill turns `cycle`'s `phases` into the cycle question; the
  review skill writes proposals as `back to <step>: ...`.

**Assumed:**
- Review (with the user) can tell when a design fix needs no test or code;
  when it is wrong, the next review finds the gap and routes it as usual.

## Constraints

- [hard] Existing `back to design:` Decisions keep today's routing.
- [hard] Deterministic: the cycle is known from review.md alone, before it
  starts.
- [hard] The Decision form check and the review gate accept the new form,
  and `finding decide` writes it.
- [soft] Plain-English syntax in the `back to <step>:` family.

## Options

### Option A: The review Decision says it (`back to design only:`)

`back to design only: ...` routes the finding to design; once design records
`done in design:`, its next step is review instead of implement. `cycle`
plans design → review when every design finding is `only` and no finding
needs a half.

- **Pros:** decided with the user when the finding is decided; the cycle
  question is accurate; no guessing.
- **Cons:** one more Decision form to learn.
- **Effort:** S
- **Touches:** `workflow` (REQ-FLOW-012, the Decision form), the review and
  build skills
- **Outcomes:** meets all three.

### Option B: The design step says it afterwards

`specworks finding done R<n> --in design --next review` records that nothing
is left for the halves.

- **Pros:** decided by the step that did the work.
- **Cons:** the cycle question still shows both halves, then shrinks; the
  subagent judges alone.
- **Effort:** S
- **Touches:** `workflow`, `cli`
- **Outcomes:** meets 1 and 3, fails 2.

### Option C: Detect it from design's commit

Skip the halves when design's commit touched only design.md.

- **Pros:** nothing to write.
- **Cons:** wrong for `add-onboarding-skill` R1, which needed code after a
  design.md-only design step.
- **Effort:** S
- **Touches:** `workflow`
- **Outcomes:** fails 2 and can break 3.

## Recommendation

Option A, agreed with the user, spelled `back to design only: ...`.

## Open Questions

- None blocking. Assumed out of scope: `only` for other steps
  (`back to specify only:`), since a spec change nearly always needs tests.

## Candidate Capabilities

- `workflow`: modified - build cycles (REQ-FLOW-012) and the Decision form
  for findings.
