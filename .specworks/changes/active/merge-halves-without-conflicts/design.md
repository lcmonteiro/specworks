# Design: merge-halves-without-conflicts

## Context

See proposal.md. `src/specworks/core/git.py` runs git (`git`, `git_text`,
`require_repo`); `src/specworks/specs/tasks.py` parses `tasks.md`;
`specworks trace --write` regenerates `traceability.md`. The build skill
merges by hand today (`specworks-build/SKILL.md` step 2).

## Goals / Non-Goals

**Goals:**
- One command that merges a half's branch and resolves only the two files
  both halves always touch (REQ-FLOW-015, REQ-CLI-010).
- Never leave a half-merged checkout: anything else aborts.

**Non-Goals:**
- Resolving any other file; rebasing; cleaning up the worktree.

## Decisions

### The merge flow

1. Refuse a dirty checkout (`git status --porcelain` not empty) or an
   unknown branch (`git rev-parse --verify <branch>`), before merging.
2. `git merge --no-ff --no-edit <branch>`. On success: done, nothing
   resolved.
3. On conflicts, list them (`git diff --name-only --diff-filter=U`). If any
   path is not the change's `tasks.md` or `traceability.md`: `git merge
   --abort`, fail naming them.
4. `tasks.md`: read both sides from the index (`git show :2:<path>`,
   `:3:<path>`); they must have the same lines once `[x]` is read as `[ ]`,
   else abort naming `tasks.md`; write each line ticked when either side
   ticks it.
5. `traceability.md`: write the trace for the merged checkout (as `trace
   --write` does).
6. `git add` the resolved files and `git commit --no-edit`.

Alternative: let git's `union` merge strategy handle `tasks.md`; it keeps
both versions of a line, so a task would appear twice. Serves: REQ-FLOW-015.

### Where it lives

The merge and its resolution in `src/specworks/workflow/merge.py` (the build's
phases live in `workflow`); the line-by-line tick merge as a function next to
it, since it is only used here. The command in `src/specworks/cli/workflow.py`.
Serves: REQ-FLOW-015, REQ-CLI-010.

## Interfaces

To be settled in the design phase. Expected:
- `src/specworks/workflow/merge.py`: `merge_branch(ws, change, branch: str) ->
  MergeResult` (new), `MergeResult(merged: bool, branch: str, resolved:
  list[Path])`, raises `MergeError` naming the conflicting files
  (REQ-FLOW-015)
- `src/specworks/workflow/merge.py`: `merge_ticks(ours: str, theirs: str) ->
  str | None` (new), None when a line differs in more than its box
  (REQ-FLOW-015)
- `src/specworks/cli/workflow.py`: `specworks merge <branch> --change <ref>
  [--json]` (new) (REQ-CLI-010)

## Risks / Trade-offs

- [`git merge --abort` fails or leaves files behind] -> the tests check the
  checkout's files and HEAD after an aborted merge.
- [Line endings differ between sides on Windows] -> compare lines without
  their line ending; write `tasks.md` with `encoding="utf-8"` and the ours
  side's line ending.
- [A tick merged from the worktree whose half did not pass its gate] -> the
  coordinator only merges after `Result: done`; `gate implement` still runs
  after the merge.

## Open Questions

None.
