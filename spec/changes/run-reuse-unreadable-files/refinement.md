# Refinement: run-reuse-unreadable-files

## Problem

Gates, validate and close reuse a test, lint or typecheck result when the
working tree's fingerprint matches an earlier run. Building that fingerprint
crashes with a raw traceback when an untracked file's name is not valid UTF-8
(reproduced: an untracked `caf\xe9.py` makes `specworks run test` fail with
`UnicodeDecodeError`). It would also crash when an untracked file can't be read
(`PermissionError`). The user is then stuck on every gate, even though their
tests pass. This was found as suspected bug 3 of `baseline-project`.

## Context

**Observed:**
- `core/runner.py`, `tree_fingerprint`: it lists untracked files with
  `git ls-files --others --exclude-standard -z`, decodes each name with a strict
  `name.decode()`, and hashes each file's content with `path.read_bytes()`.
  Neither step handles an error. It returns `None` (meaning "run for real")
  only when git itself fails or a submodule holds untracked files.
- `core/runner.py`, `cached_run`: a `None` fingerprint means no reuse, and the
  command runs for real.
- Living spec of `project`, REQ-PROJ-014: reuse is off without git, with
  `SPECWORKS_RUN_CACHE=0`, and when a submodule holds untracked files.
  AC-PROJ-014.2 says the content of untracked files counts.
- Tests: `tests/test_run_cache.py` (the AC-PROJ-014.x tests) count real runs
  with a counter file.

**Assumed:**
- An unreadable untracked file is rare, but possible: a file of another user, a
  socket, or a file removed between listing and reading.
- The container runs as root, so the permission case can't be reproduced here
  with file modes. A test can simulate the read failure instead.

## Constraints

- [hard] No traceback: a gate never crashes because of an untracked file.
- [hard] Never reuse a result when a file's content can't be seen; a stale
  "same code" result is worse than a slower run.
- [soft] Keep reuse working whenever the fingerprint can still be exact.

## Options

### Option A: Run for real whenever in doubt

Any untracked file with an undecodable name, or that can't be read, makes the
fingerprint unknown (`None`), so the command runs for real.

- **Pros:** One rule, the same as "git cannot tell". Smallest change.
- **Cons:** A repository that keeps an oddly named file never reuses runs.
- **Effort:** S
- **Touches:** `project`

### Option B: Exact names, run for real only when content is unreadable

Names are used as raw bytes (`os.fsdecode`, so any name the file system allows
works), so oddly named files are fingerprinted like any other and reuse keeps
working. An untracked file that can't be read makes the fingerprint unknown, so
the command runs for real.

- **Pros:** No crash, never a stale result, and reuse is lost only when a file
  truly can't be seen.
- **Cons:** Two cases to handle and test instead of one.
- **Effort:** S
- **Touches:** `project`

### Option C: Fingerprint unreadable files by size and modification time

- **Pros:** Reuse never stops.
- **Cons:** An edit that keeps the size and time would reuse a stale result,
  which breaks the hard constraint.
- **Effort:** S
- **Touches:** `project`

## Recommendation

**Option B**, chosen with the user. It removes both crashes, never shows a stale
result, and turns reuse off only when a file's content really can't be seen,
which is what REQ-PROJ-014 already does for submodules.

## Open Questions

None.

## Candidate Capabilities

- `project`: REQ-PROJ-014 MODIFIED, with two new criteria: an oddly named
  untracked file is fingerprinted and reused like any other, and an untracked
  file that can't be read means a real run, not a crash.
