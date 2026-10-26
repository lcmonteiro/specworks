# Proposal: drop-review-finish-run

## Why

In `/specworks-build` step 3, after the user decides the review findings, a
fresh review subagent runs to tick earlier-cycle findings, finish review.md
and gate it. In the last builds it never ticked anything (the review's
first run of the cycle already had) and only re-ran the gate. The
refinement chose Option A: drop that run.

## What Changes

- `specworks-build/SKILL.md` step 3:
  - "First run" also ticks the findings from an earlier cycle that are now
    done (`- [x]`, with what was done) before it returns the new ones.
  - After the coordinator has written every `**Decision**:` line, it runs
    `specworks gate review --change "<ref>" --allow-open` itself; no second
    review subagent runs. If the gate rejects a Decision line, the
    coordinator fixes its own line and runs the gate again.
  - The special case "when every finding is decided `accepted` ..." goes:
    it is now the only path.
- `tests/test_skills.py`: the wording check for the build skill follows the
  new text (the coordinator runs the gate itself after the decisions; no
  "fresh review subagent" after them). Installed copies refreshed with
  `specworks skills`.
- Assumption: review.md's summary is not rewritten after the decisions; the
  Decision lines carry them.

## Capabilities

None: skill text only; the change is marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- `src/specworks/skills/specworks-build/SKILL.md` and its installed copies,
  `tests/test_skills.py`. No CLI change.

## Out of Scope

- The review skill itself, run on its own (it asks the user directly).
- The other phases' subagent flow.
