# Proposal: commit-command

## Why

Each phase's work is committed by hand: the agent picks the files from
`git status` and memory and builds the `git add … && git commit …` command
itself, which is slow, can let unrelated work in or leave a phase file out,
and differs between skills. The refinement chose Option A: record the dirty
files when a phase starts, and commit what changed since then.

## What Changes

- When a change's phase changes (`specworks new`, `start`, `phase`),
  `.change.yaml` records the workspace's dirty and untracked files (git's
  view: staged, unstaged, new; ignored files are not listed) with a SHA-256
  of each file's content, or `deleted` for a deleted one. Moving to the
  phase a change is already in keeps the record it has.
- `specworks commit --change <ref> [--message <subject>] [--trailer
  "Key: value"]... [--json]` commits, from the workspace root:
  - the change folder, and every dirty or untracked file that is not in the
    record or whose content differs from it;
  - with the message `<ref>: <phase>` (or `--message`), a blank line and the
    trailers in order;
  - it lists the dirty files it left out (unchanged since the phase
    started), and flags a committed file that was already dirty when the
    phase started;
  - with nothing to commit it says so, exits 0 and creates no commit;
  - it never pushes, and refuses a detached HEAD and a ref outside the
    workspace's changes.
- `_shared/committing.md` (included by 7 skills) says to commit with
  `specworks commit --change "<ref>"`, adding the project's trailers with
  `--trailer`, and to report the files it left out. Installed copies
  refreshed with `specworks skills`.
- Assumptions:
  - paths are relative to the workspace root, as in every command;
  - a test half's worktree has its own working tree, and its record is the
    one in its own copy of `.change.yaml`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `project`: new REQ-PROJ-023 (the record of dirty files at a phase move)
  and REQ-PROJ-024 (committing a phase).
- `cli`: new REQ-CLI-012 (`specworks commit`).

## Impact

- `src/specworks/core/changes.py` (the record, written with the phase),
  `src/specworks/core/git.py` (status, staging and committing), a CLI
  command in `src/specworks/cli/changes.py`, `_shared/committing.md` and the
  installed skills, `tests/`.

## Out of Scope

- Pushing (only `/specworks-close` and `/specworks-done` offer it).
- Splitting a file's edits from before and during the phase.
- Commits for merges (`specworks merge` keeps its own).
- The rest of the `deterministic-steps` sequence.
