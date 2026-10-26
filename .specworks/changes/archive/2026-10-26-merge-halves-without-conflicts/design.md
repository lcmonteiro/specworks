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

Agreed with the user (BranchMergeError, as proposed)

- `src/specworks/workflow/merge.py`: `merge_branch(ws: Workspace, module: Module,
  change: Change, branch: str) -> MergeResult` (new): refuses a dirty checkout
  or an unknown branch, merges, resolves `tasks.md` and `traceability.md`,
  commits; raises `BranchMergeError`, and `GitError` (from `require_repo`)
  outside a git repository. `module` gives the change's ref for the
  regenerated trace (REQ-FLOW-015)
- `src/specworks/workflow/merge.py`: `MergeResult(merged: bool, branch: str,
  resolved: list[Path])` (new, frozen dataclass), with `to_dict(ws) -> dict`
  giving `merged`, `branch` and `resolved` as workspace-relative paths;
  `merged` is False only when git had nothing to merge ("Already up to date")
  (REQ-FLOW-015, REQ-CLI-010)
- `src/specworks/workflow/merge.py`: `BranchMergeError(SpecworksError)` (new)
  with `files: list[Path]`, the conflicting files (empty when refused before
  merging: uncommitted changes, unknown branch). Named apart from the existing
  `specworks.specs.merge.MergeError`, which close raises (REQ-FLOW-015)
- `src/specworks/workflow/merge.py`: `merge_ticks(ours: str, theirs: str) ->
  str | None` (new): `tasks.md` with each line ticked when either side ticks
  it, `None` when a line differs in more than its box (REQ-FLOW-015)
- `src/specworks/cli/workflow.py`: `specworks merge <branch> --change <ref>
  [--json]` (new): `--json` prints the change's fields plus `merged`,
  `branch`, `resolved`; errors are values through the app's error wrapper
  (REQ-CLI-010)

No existing interface changes; nothing is BREAKING.

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
