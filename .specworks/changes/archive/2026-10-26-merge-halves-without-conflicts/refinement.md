# Refinement: merge-halves-without-conflicts

## Problem

In `/specworks-build` the test half runs in a git worktree and the code half
in the main checkout. Both tick their tasks in the same `tasks.md` and both
rewrite `traceability.md`, so merging the worktree's branch conflicts in
those two files on every build (all four builds so far). The coordinator
resolves it by hand each time, with the same mechanical rule: a task is done
when either side ticked it, and the trace is regenerated.

## Context

**Observed:**
- `specworks task done|undo` ticks tasks; `gate test` and `gate code` require
  every task of their own half ticked, so a half cannot leave its ticks out.
- Both halves run `specworks trace --write` at the end of their skill.
- `specworks-build/SKILL.md` step 2 tells the coordinator to `git merge
  <branch>`, keep every tick on a `tasks.md` conflict, take either side of
  `traceability.md` and regenerate it, and stop on any other conflict ("a
  half worked outside its own files"), then run `gate implement`.
- `src/specworks/specs/tasks.py` parses `tasks.md` (`Task.done`, `Task.half`);
  `src/specworks/core/git.py` wraps git commands.
- In the last builds git's rename detection carried edits across a moved
  change folder, and `.change.yaml` never conflicted (both halves write the
  same phase).

**Assumed:**
- The conflicting `tasks.md` lines differ only in their box (`[ ]` vs
  `[x]`); a line whose text differs is a real conflict.

## Constraints

- [hard] One `tasks.md` per change; its format does not change.
- [hard] On any conflict outside `tasks.md` and `traceability.md`, the merge
  is aborted (`git merge --abort`): the checkout is left as it was, the
  command exits 1 and names the conflicting files.
- [hard] The command writes only inside the git merge it runs: no ticks the
  halves did not make, no other edits.
- [soft] The build skill calls the command instead of describing the manual
  resolution.

## Options

### Option A: the test half commits no tasks.md / traceability.md

Skill text only; the coordinator ticks the `[test]` tasks after the merge.

- **Pros:** no CLI change.
- **Cons:** ticks written twice; relies on the skill being followed.
- **Effort:** S
- **Touches:** skills

### Option B: `specworks merge <branch> --change <ref>`

Runs `git merge`; when the only conflicts are in the change's `tasks.md`
and `traceability.md`, keeps every tick (a line is done when either side
ticked it), regenerates the trace and commits the merge; any other conflict
aborts the merge and is reported. The build skill calls it.

- **Pros:** deterministic and tested; one call for the coordinator; no
  format change.
- **Cons:** a new command and git-merge handling with its tests.
- **Effort:** M
- **Touches:** `workflow` (or `specs` for the tick merge), `cli`, skills

### Option C: a git merge driver for tasks.md

- **Pros:** works for any merge.
- **Cons:** needs per-clone git config; fails silently without it; does not
  cover `traceability.md`.
- **Effort:** M
- **Touches:** `integrations`, `cli`

### Option D: two task files (test and code)

Discussed and set aside: it removes the `tasks.md` conflict but not the
`traceability.md` one, splits each requirement's plan across files and
changes the format every tool reads.

## Recommendation

Option B, chosen by the user, with one `tasks.md` and the merge aborted on
any other conflict.

## Open Questions

- Which capability owns the tick merge (`specs`, where `tasks.md` is parsed,
  or `workflow`, where the build's phases live): specify decides.
- The exact output (`--json` shape, the merge commit message): specify
  decides.

## Candidate Capabilities

- `workflow`: modified - merging the test half's branch.
- `cli`: modified - the `specworks merge` command.
- `specs`: possibly modified - merging the ticks of two `tasks.md` versions.
