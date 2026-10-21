# Refinement: track-suspected-bugs

## Problem

While adopting a project, each baseline finds behaviour that looks like a bug,
and today those findings get lost. In the user's words: "during the adoption
if you find possible bugs create a new artifact. Continue the normal process
by adding capabilities and in the end we can do also a foreach bug and fix
with the normal flow". Adopting this repository found 13 such bugs. They were
tracked only in the conversation, by number ("bug 11"), which does not survive
a new session or a hand-over.

## Context

**Observed:**
- `/specworks-baseline` (`src/specworks/skills/specworks-baseline/SKILL.md`)
  keeps a list of suspected bugs in step 3. Step 4 writes them under the
  baseline proposal's Out of Scope, and the user confirms them along with the
  requirements. Step 9 only says "The suspected bugs can each start with
  `/specworks-refine`".
- Once the baseline closes, its proposal goes to `spec/changes/archive/`.
  Nothing lists those bugs again.
- `/specworks-adopt` (`src/specworks/skills/specworks-adopt/SKILL.md`) shows
  the loop `for each capability: baseline, done`. It has no step for bugs.
- `specworks new <name> [--module m]` creates a change in phase refine.
  `specworks list` / `context` show changes in flight, with their phase.
  `specworks abandon` archives a change without building it.
- `/specworks-refine` updates an existing `refinement.md` rather than
  overwriting it.
- The skills capability was removed until the project decides how to tag and
  test skills. No capability holds requirements for skill text.

**Assumed:**
- A parked change in phase refine blocks no other change: gates, validate
  and close each look at one change only.

## Constraints

- [hard] A baseline still changes no behaviour. It records bugs and never
  fixes them.
- [hard] Only bugs the user confirms at baseline step 4 become changes.
- [hard] Fixing a bug follows the normal flow: refine → specify → build → done.
- [soft] No new CLI concept or artifact type; reuse changes.
- [soft] The installed copies (`.claude/skills`, `.github/skills`) follow the
  packaged skills, refreshed with `specworks skills`.

## Options

### Option A: a change per bug

At step 4, once the user confirms, the baseline runs `specworks new
fix-<short-name>` (with `--module` for another module) for each bug. It writes
the change's `refinement.md` with what was seen: the capability, the file and
test, the observed versus the expected behaviour, and that the baseline of
`<capability>` found it. Options and Recommendation stay "Pending". The
baseline proposal's Out of Scope names each change by its ref.

When every capability has a living spec, step 9 of the last baseline lists the
waiting `fix-*` changes in phase refine, together with the loop:
`/specworks-refine fix-x`, `/specworks-specify`, `/specworks-build`,
`/specworks-done`. Adopt's overview shows the same final loop. A change that
turns out not to be a bug is closed with `specworks abandon`.

- **Pros:** reuses changes, `list` and `abandon`; nothing new to learn. Each
  bug survives sessions and carries its evidence into its own refinement.
- **Cons:** many changes in flight during adoption. The baseline writes into
  another change's folder.
- **Effort:** S (skill text only).
- **Touches:** packaged skills `specworks-baseline` and `specworks-adopt`
  (no capability).

### Option B: one backlog file

Each baseline appends an entry (capability, evidence, status) to one file in
the workflow folder. At the end, a loop creates a change for each open entry.

- **Pros:** one index of every suspected bug.
- **Cons:** a new artifact type, with CLI support to list and close entries;
  its state can drift from the changes made from it.
- **Effort:** M.
- **Touches:** `project`, `cli`, packaged skills.

### Option C: both

The backlog file is the index and the parked changes are the work.

- **Pros:** an index and durable work items.
- **Cons:** two records of the same thing to keep in sync; Option B's cost.
- **Effort:** M.
- **Touches:** as Option B.

## Recommendation

Option A, chosen by the user. Two smaller decisions follow from it:
- The bug changes are created after the user confirms the bug list at
  baseline step 4.
- The final "for each bug" loop lives in baseline step 9 (when no capability
  is left without a living spec) and in adopt's overview. There is no new
  skill.

## Open Questions

None blocking. The change only edits skill text, and no capability holds
requirements for it, so it is likely a `skip-specs` change (the specify phase
decides).

## Candidate Capabilities

- None: the packaged skills `specworks-baseline` and `specworks-adopt`
  change, and the skills capability is deferred.
