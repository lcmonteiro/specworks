# Proposal: review-deleted-files

## Why

`specworks review` drops files deleted on the branch, so deleted code is never
reviewed. A requirement the change doesn't touch can silently lose its only
code (suspected bug 5 of `baseline-workflow`; refinement.md, option B).

## What Changes

- `specworks review` lists each file deleted on the branch in `changedFiles`,
  with kind `deleted` and the kind it had (`was`: `source`, `test` or `other`).
- Deleted source and test files are a new drift candidate, `deletedFiles`,
  counted in `findingCount`.
- The review gate (and validate, which shares the check) requires each deleted
  source or test file to be named under "Changed files without tags" in
  review.md, as for untagged changed files. Deleted docs and config are listed
  only.
- Files that still exist are reported exactly as today.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workflow`: REQ-FLOW-009 "Drift report" MODIFIED (new AC-FLOW-009.7, deleted
  files listed) and REQ-FLOW-011 "Gate review" MODIFIED (new AC-FLOW-011.6, a
  deleted file must be accounted for).

## Impact

- `src/specworks/workflow/review.py`: `changed_paths`, `ChangedFile`,
  `ReviewReport`.
- `src/specworks/workflow/checks.py`: `files_accounted`.
- `src/specworks/cli/workflow.py`: the label of the new finding in the text
  output of `specworks review`.
- `tests/test_review_phase.py`.

The JSON output of `specworks review` gains a `deletedFiles` key and an
optional `was` field. Existing keys are unchanged.

## Out of Scope

- Detecting automatically that a requirement lost its only code or test
  (option C, a possible follow-up).
- Renames: git reports a rename as a deletion plus an addition, so the old path
  is listed as deleted and the new one as changed. Following renames is left
  out.
