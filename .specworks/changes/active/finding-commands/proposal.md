# Proposal: finding-commands

## Why

Every line of a change's `review.md` is written by hand (new findings,
Decisions, `done in <step>:` lines, ticks), with ad-hoc scripts, and a
malformed line only shows up when `gate review` runs. The refinement chose
Option A: four CLI commands that edit the text in place and check the result.

## What Changes

- New command group `specworks finding`, each with `--change <ref>` and
  `--json`:
  - `finding add <type> "<text>" --proposal "<proposal>"`: appends
    `- [ ] R<next> **<type>** <text>` and `  - **Proposal**: <proposal>`
    under `## Findings` (the next free ID); creates review.md from its
    template when missing; refuses an unknown type.
  - `finding decide R<n> "<decision>"`: writes the finding's
    `  - **Decision**: <decision>` line, replacing one already there; the
    decision must start `back to <step>:` (specify, design, implement, test,
    code) or `accepted:`; `accepted` ticks the box.
  - `finding done R<n> --in <step> "<what>"`: adds
    `  - done in <step>: <what>`.
  - `finding close R<n> "<what was confirmed>"`: ticks the box and adds
    `  - confirmed in review: <what was confirmed>`.
  - Each refuses an unknown finding, step or type and an empty text, writes
    only after the edited file reads back with the expected finding, and
    otherwise leaves the file unchanged; under `--json` it prints the finding
    as `specworks cycle` sees it, errors as `{"error": …}` with exit 1.
- Skills: `specworks-review` (findings, ticks, confirmations),
  `specworks-build` step 3 and `_shared/phase-subagents.md` (Decisions),
  `specworks-specify` step 2 and the design, test and code skills ("done in"
  lines) use the commands instead of editing review.md. Installed copies
  refreshed with `specworks skills`.
- Assumptions:
  - the confirmation line reads `confirmed in review: …`; the parser ignores
    it (only the box counts), so nothing it reads changes;
  - lines are added at the end of the finding's block, after its existing
    indented lines.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `workflow`: new REQ-FLOW-016, writing findings and their follow-ups to
  review.md.
- `cli`: new REQ-CLI-011, the `finding` commands.

## Impact

- `src/specworks/workflow/review.py` (writers next to `parse_review`), a new
  `src/specworks/cli/` module or `review.py`'s CLI, the skills above and
  their installed copies, `tests/`.

## Out of Scope

- Changing how review.md is read (REQ-FLOW-010) or gated (REQ-FLOW-011).
- Deleting or renumbering findings.
- The rest of the `deterministic-steps` sequence.
