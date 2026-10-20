# Tasks: run-reuse-unreadable-files

## 1. Untracked files the fingerprint struggles with

- [ ] 1.1 Write failing tests in `tests/test_run_cache.py` for AC-PROJ-014.7 (an untracked file named `caf\xe9.py`, two gate runs) and AC-PROJ-014.8 (reading one untracked file raises `PermissionError`, two gate runs) tagged `@ac`; verify they fail with the crash, not for another reason
- [ ] 1.2 In `tree_fingerprint`, take untracked names as raw bytes (`os.fsdecode`) and return no fingerprint when an untracked file cannot be read (REQ-PROJ-014) tagged `@req REQ-PROJ-014`; verify the 1.1 tests and the existing AC-PROJ-014.x tests pass
