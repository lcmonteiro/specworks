# Refinement: drop-review-finish-run

## Problem

In `/specworks-build` step 3, after the user decides the review findings, a
fresh review subagent runs to tick earlier-cycle findings that are done,
finish review.md and gate it (skipped only when every finding is
`accepted`). In the last builds it never ticked anything: it only updated
the summary and re-ran the gate, each time a full subagent start.

## Context

**Observed:**
- `src/specworks/skills/specworks-build/SKILL.md` step 3: "First run" writes
  review.md with every finding open and returns them; "You" ask the user and
  write each `**Decision**:` line; "Then a fresh review subagent reads the
  decided review.md, ticks the findings from an earlier cycle that are now
  done ..., finishes the file and gates it", skipped when every finding is
  `accepted` (the coordinator then runs `specworks gate review --change
  "<ref>" --allow-open` itself).
- In `move-config-into-spec-folder` and `merge-halves-without-conflicts`,
  the finish run ran three times; each time the review's first run of that
  cycle had already ticked the earlier-cycle findings (e.g. "R1 confirmed in
  review cycle 2"), and the finish run only re-gated.
- `tests/test_skills.py::test_build_gates_the_review_itself_when_every_finding_is_accepted`
  checks the wording ``run `specworks gate review --change "<ref>"
  --allow-open` yourself``.
- `_shared/phase-subagents.md` routes each review answer to the finding's
  `**Decision**:` line; unchanged.

**Assumed:**
- The review skill's own steps let its first run tick earlier-cycle findings
  (they did in every cycle so far).

## Constraints

- [hard] No behaviour change in the CLI: skill text only (`skip-specs`).
- [hard] The review gate still runs after the decisions, with
  `--allow-open`.
- [hard] The coordinator still writes only the user's answers: the Decision
  lines (and fixes its own line if the gate rejects it).

## Options

### Option A: drop the finish run

The first review run ticks earlier-cycle findings (step 3 says so
explicitly); after writing every Decision, the coordinator runs the review
gate itself.

- **Pros:** simplest flow; one subagent start fewer per round of decisions;
  matches what every build needed.
- **Cons:** review.md's summary is not rewritten after the decisions.
- **Effort:** S
- **Touches:** skills (no capability)

### Option B: skip it unless something is left to tick

- **Pros:** keeps a fallback.
- **Cons:** a conditional rule for a case that has not occurred.
- **Effort:** S

### Option C: keep it

- **Pros:** no change.
- **Cons:** a no-op subagent run after every round of decisions.

## Recommendation

Option A, chosen by the user.

## Open Questions

None.

## Candidate Capabilities

- None: skill text only (`skip-specs`).
