# Review: fix-commit-after-close

Base: `origin/main`

## Findings

- [ ] R1 **test-gap** AC-PROJ-024.7 is tested only for an active change (tests/test_commit.py:375); for a change close has archived, the exclusion of its former active folder from already_dirty (src/specworks/core/changes.py:216) has no test: replacing it with own = (folder,) passes every test, and that is the case close hits (the active .change.yaml is recorded dirty when close starts, then deleted by the archive)
  - **Proposal**: back to test: in the closed fixture record the active .change.yaml as dirty when close starts (as specworks start close does), then assert it is committed and already_dirty / alreadyDirty is empty in the AC-PROJ-024.6 and AC-CLI-012.4 tests
  - **Decision**: back to test: the closed fixture records the active .change.yaml as dirty when close starts, and the AC-PROJ-024.6 and AC-CLI-012.4 tests assert it is committed and already_dirty / alreadyDirty is empty (agreed with the user)
  - done in test: the closed fixture moves the change to validate then close without committing, so close's record names the active .change.yaml as dirty; the AC-PROJ-024.6 test asserts it is in the record, committed and already_dirty is empty, and the AC-CLI-012.4 test asserts alreadyDirty is empty; with own = (folder,) both now fail

## Changed files without tags

None: `specworks review` lists no untraced source or test files.

## Summary

The suite (752 tests) and lint pass; the code does what REQ-PROJ-024 and
REQ-CLI-012 say and follows design.md (no interface changes). One test-gap:
the already-dirty exclusion of an archived change's former active folder,
the case close actually hits, has no test. It goes back to the test half.
