# Refinement: review-deleted-files

## Problem

`specworks review` never shows files deleted on the branch, so deleted code is
never reviewed. If a branch deletes a file carrying `@req REQ-X` for a
requirement the change doesn't touch, that requirement silently loses its code:
the trace, review, the gates and validate only check the change's own
requirements. This was found as suspected bug 5 of `baseline-workflow`.

## Context

**Observed:**
- `workflow/review.py`, `changed_paths`: takes every name from
  `git diff --name-only <since>` plus untracked files, then keeps only those
  that still exist (`path.is_file()`). Deleted files are dropped there.
- `review_change` classifies each changed file with `changed_file_kind`
  (`source`, `test`, `other`; workflow folders left out) using `scan_rule`,
  which works from the path alone.
- `ReviewReport.untraced_source` / `untraced_tests` feed `findings()`. The
  review gate's `files_accounted` check (and validate's) requires each of them
  to be named under "Changed files without tags" in review.md.
- `specs/trace.py`: the matrix and its gaps cover only the change's own delta
  requirements. Code removed for other requirements is invisible everywhere.
- Living spec of `workflow`: REQ-FLOW-009 (drift report) and REQ-FLOW-011 (gate
  review).

**Assumed:**
- Most deletions are harmless (dead code, a refactor that moved code). One line
  in review.md per deleted code or test file is an acceptable cost.

## Constraints

- [hard] A deleted source or test file never passes review unseen.
- [hard] Files that still exist are reported exactly as today.
- [soft] Reuse the existing "accounted for" mechanism, with no new review.md
  section.

## Options

### Option A: Keep it, and document it

State in REQ-FLOW-009 that only existing files are compared.

- **Pros:** No code change.
- **Cons:** The blind spot stays.
- **Effort:** S
- **Touches:** `workflow`

### Option B: List deleted files, require them accounted for

`specworks review` lists each file deleted on the branch with kind `deleted`
and the kind it had (`source`, `test` or `other`). A deleted source or test
file is a drift candidate (`deletedFiles`), and the review gate and validate
require it to be named under "Changed files without tags" with a reason.
Deleted docs and config are listed only.

- **Pros:** Every deleted code or test file gets a human look. Reuses the
  existing accounting.
- **Cons:** One line in review.md per deleted code or test file, even dead code.
- **Effort:** S
- **Touches:** `workflow`

### Option C: Flag lost coverage automatically

Read each deleted file's tags at the base commit, and report a requirement that
still exists but has lost its only code or test.

- **Pros:** Catches exactly the risky case, with no busywork.
- **Cons:** More code (reading files from the base commit, checking for other
  coverage). Could come later on top of B.
- **Effort:** M
- **Touches:** `workflow`, `specs`

## Recommendation

**Option B**, chosen with the user. It closes the blind spot with the mechanism
review already has, and leaves the judgement (refactor or lost requirement) to
the reviewer.

## Open Questions

None.

## Candidate Capabilities

- `workflow`: REQ-FLOW-009 MODIFIED (the drift report lists deleted files) and
  REQ-FLOW-011 MODIFIED (a deleted source or test file must be accounted for).
