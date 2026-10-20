# Review: run-reuse-unreadable-files

Base: `origin/main`

## Findings

None.

Checked against REQ-PROJ-014 (MODIFIED) and its new criteria:
- AC-PROJ-014.7: `tree_fingerprint` builds each untracked path with
  `os.fsdecode(name)`, so a name that isn't UTF-8 no longer raises. The digest
  still hashes the raw name bytes, so reuse stays exact. The test creates
  `src/auth/caf\xe9.py`, runs the gate twice, and asserts one real run and a
  reused second result. It is skipped on file systems that refuse such names.
- AC-PROJ-014.8: an `OSError` while reading an untracked file returns `None`,
  so `cached_run` runs the command for real and records nothing for that tree.
  A stale result can't be reused. The test simulates `PermissionError` (the
  container runs as root) and asserts two real runs.
- Before the fix, both tests failed with the crash (`UnicodeDecodeError`,
  `PermissionError`). After it, all 14 tests in `tests/test_run_cache.py` pass,
  including AC-PROJ-014.1 to .6.
- The modified requirement's test file (`tests/test_run_cache.py`) changed on
  the branch, as the review gate expects.

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

Fingerprinting untracked files no longer crashes: odd names are fingerprinted
exactly, and an unreadable file means a real run. No drift.
