# Proposal: track-suspected-bugs

## Why

The suspected bugs a baseline finds are written only into its proposal's Out of
Scope, and that proposal is archived when the baseline closes. Nothing brings
them back after adoption: the 13 bugs found while adopting this repository were
tracked only in the conversation. Following the refinement (Option A), each
confirmed bug becomes a change of its own. The change waits in phase refine
while adoption goes on. Once every capability is baselined, each one is fixed
through the normal flow.

## What Changes

- `/specworks-baseline` step 3: for each suspected bug, record the evidence
  (where it shows, observed versus expected behaviour).
- `/specworks-baseline` step 4: the user confirms the list of suspected bugs
  along with the requirements. For each confirmed bug, the baseline runs
  `specworks new fix-<short-name>` (with `--module` when the bug belongs to
  another module). It then writes that change's `refinement.md` from the
  `refinement` instructions: Problem and Context filled from the evidence,
  naming the baseline that found it; Options and Recommendation left
  "Pending". The baseline proposal's Out of Scope names each bug by its change
  ref. Bugs the user rejects get no change.
- `/specworks-baseline` step 9: when no capability is left without a living
  spec, list the changes waiting in phase refine that baselines created
  (`specworks list --json`). Hand over to the loop `for each: /specworks-refine
  <ref>, /specworks-specify <ref>, /specworks-build <ref>, /specworks-done
  <ref>`. A change that turns out not to be a bug is closed with
  `specworks abandon <ref>`.
- `/specworks-baseline` boundary and guardrails: creating a bug's change and
  its `refinement.md` is the only writing outside the baseline's own change
  folder; it still fixes nothing.
- `/specworks-adopt`: the overview loop and the final report gain the closing
  "for each suspected bug" loop.
- The installed copies (`.claude/skills`, `.github/skills`) are refreshed with
  `specworks skills`.

## Capabilities

None: only the packaged skill text changes, and no capability holds
requirements for the skills. The skills capability was set aside until the
project decides how to tag and test skills. The change is marked
`skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- `src/specworks/skills/specworks-baseline/SKILL.md`,
  `src/specworks/skills/specworks-adopt/SKILL.md`, and their installed copies
  in `.claude/skills/` and `.github/skills/`.
- No CLI, API or data change. The skill rendering tests (`tests/test_skills.py`)
  must still pass.

## Out of Scope

- A backlog file or a new artifact type for bugs (Options B and C of the
  refinement).
- A CLI marker that tells a bug change apart from others; the `fix-` prefix
  and the refinement's text are enough for now.
- Fixing any bug during a baseline: it stays a no-behaviour-change step.
- Tagging and testing skill text (the deferred skills capability).
