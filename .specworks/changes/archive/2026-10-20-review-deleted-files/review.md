# Review: review-deleted-files

Base: `origin/main`

## Findings

None.

Checked against REQ-FLOW-009 and REQ-FLOW-011 (MODIFIED) and design.md:
- AC-FLOW-009.7: `deleted_paths` returns the changed names that no longer exist
  under the workspace. `review_change` lists each one as
  `ChangedFile(kind="deleted", was=<its kind>)`, workflow folders left out, and
  `ReviewReport.deleted_files` (those that were source or test) is reported as
  `deletedFiles`. The test deletes a source file, a test and a doc, and checks
  all three are listed with their former kind and only the first two are
  findings.
- AC-FLOW-011.6: `files_accounted` (shared by the review gate and validate) now
  also requires `deleted_files` under "Changed files without tags". The test
  sees the gate fail listing both files, then pass once they are named.
- Existing files are reported as before: `changed_paths` keeps its signature
  and result, now through `_changed_names`, which it shares with
  `deleted_paths`. All 26 review tests pass, and so do the full suite and lint.
  The text output of `specworks review` prints the new line ("deleted code and
  test files"), and `tests/test_walkthrough.py` exercises it.
- The interfaces match design.md: `deleted_paths`, `ChangedFile.was` (in
  `to_dict` only when set), `ReviewReport.deleted_files`.
- Edge noted, not drift: a changed file that is now a dangling symlink used to
  be dropped. It is now listed as deleted, which is the more conservative
  behaviour.

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

Deleted files now show in the drift report, and deleted code or tests must be
accounted for in review.md like untagged changed files. No drift.
