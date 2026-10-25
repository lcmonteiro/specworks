# Design: review-deleted-files

## Context

`changed_paths` (`src/specworks/workflow/review.py`) lists the files changed
since the base and drops those that no longer exist. See proposal.md for why.

## Goals / Non-Goals

**Goals:**
- Show deleted files in the drift report and make deleted code or tests count
  in the review gate's accounting (REQ-FLOW-009, REQ-FLOW-011).

**Non-Goals:**
- Detecting lost requirement coverage, and following renames.

## Decisions

### A separate list of deleted paths

A new `deleted_paths(ws, since)` returns the names git reports as changed
whose file no longer exists, under the workspace and outside workflow folders.
It uses the same `git diff --name-only -z` call as `changed_paths`, which stays
as it is, so existing files are reported exactly as before. The alternative,
returning both lists from `changed_paths`, would change a signature other code
calls for no gain. Serves: REQ-FLOW-009.

### Deleted files are `ChangedFile`s with kind `deleted`

Each one is a `ChangedFile(kind="deleted", was=<its kind>)`, where `was` comes
from `changed_file_kind`, which works from the path alone. `ReviewReport`
gains `deleted_files` (those that were source or test), reported as
`deletedFiles` and accounted for by `files_accounted`, next to the untraced
files. Serves: REQ-FLOW-009, REQ-FLOW-011.

## Interfaces

- `src/specworks/workflow/review.py`: `deleted_paths(ws: Workspace, since: str) -> list[str]` (new)
- `src/specworks/workflow/review.py`: `ChangedFile.was: str = ""` (new field, set for kind `deleted`; in `to_dict` only when set)
- `src/specworks/workflow/review.py`: `ReviewReport.deleted_files -> list[str]` (new property; `findings()` gains `deletedFiles`)
- `src/specworks/workflow/checks.py`: `files_accounted` also requires `deleted_files`

## Risks / Trade-offs

- [A rename shows up as a deletion] -> one line in review.md, and the new path
  is still checked for tags as today.
