# Proposal: merge-halves-without-conflicts

## Why

In `/specworks-build` the test half's worktree branch conflicts with the
main checkout in `tasks.md` and `traceability.md` on every build, because
both halves tick tasks and rewrite the trace. The coordinator resolves it by
hand with the same mechanical rule each time. The refinement chose Option B:
a `specworks merge` command that does that resolution, and aborts on any
other conflict.

## What Changes

- New command `specworks merge <branch> --change <ref>`: merges `<branch>`
  into the current checkout with git.
  - When the merge has no conflict, it is committed as git makes it.
  - When the only conflicts are in the change's `tasks.md` and
    `traceability.md`: `tasks.md` keeps every tick (a task is done when either
    side ticked it), `traceability.md` is regenerated, and the merge is
    committed.
  - Any other conflict, or a `tasks.md` line that differs in more than its
    box, aborts the merge (`git merge --abort`): the checkout is left as it
    was, the command exits 1 and names the conflicting files.
  - It refuses before merging when the checkout has uncommitted changes, the
    branch does not exist, or the folder is not in a git repository.
  - It prints what it resolved (`--json`: `merged`, `branch`, `resolved`).
- `/specworks-build` step 2 calls `specworks merge` instead of describing
  the manual resolution, and stops on its error as today.
- Assumption: the merge commit keeps git's default message
  (`Merge branch '<branch>'`).

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `workflow`: new REQ-FLOW-015 (merging a half's branch).
- `cli`: new REQ-CLI-010 (the `merge` command).

## Impact

- `src/specworks/workflow` (the merge and its resolution),
  `src/specworks/core/git.py` (git calls), `src/specworks/cli` (the
  command), `src/specworks/skills/specworks-build/SKILL.md` and its installed
  copies, tests.
- No change to the `tasks.md` format or to the other commands.

## Out of Scope

- Two task files, or a git merge driver.
- Resolving conflicts in any other file, or rebasing.
- Removing the worktree or its branch after the merge.
