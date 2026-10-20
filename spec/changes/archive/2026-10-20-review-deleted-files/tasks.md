# Tasks: review-deleted-files

## 1. Deleted files in the drift report

- [x] 1.1 Add `deleted_paths`, `ChangedFile.was` and `ReviewReport.deleted_files` as stubs (REQ-FLOW-009); verify the existing tests still pass
- [x] 1.2 Write a failing test in `tests/test_review_phase.py` for AC-FLOW-009.7 (the branch deletes a source, a test and a doc) tagged `@ac`; verify it fails because deleted files aren't listed
- [x] 1.3 Implement `deleted_paths`, list deleted files with kind `deleted` and `was`, report `deletedFiles` (REQ-FLOW-009) tagged `@req REQ-FLOW-009`; verify the 1.2 test passes

## 2. Deleted files in the review gate

- [x] 2.1 Write a failing test for AC-FLOW-011.6 (a deleted source file not named under "Changed files without tags", then named) tagged `@ac`; verify it fails because the gate passes without naming it
- [x] 2.2 Make `files_accounted` require `deleted_files` too (REQ-FLOW-011) tagged `@req REQ-FLOW-011`; verify the 2.1 test passes and the full suite is green
