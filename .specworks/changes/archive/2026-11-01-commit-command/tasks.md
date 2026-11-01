# Tasks: commit-command

## 1. The record of dirty files

- [x] 1.1 Add the stubs in design.md's Interfaces: `dirty_files` and `commit` in `src/specworks/core/git.py`, `Change.dirty`, the `root` parameter of `set_phase`, `CommitResult` and `commit_phase` in `src/specworks/core/changes.py` (REQ-PROJ-023, REQ-PROJ-024); verify `specworks run lint` passes
- [x] 1.2 [test] Tests for AC-PROJ-023.1 (modified, untracked and deleted files recorded with their SHA-256 or `deleted` at a phase move), AC-PROJ-023.2 (moving to the same phase keeps the record) and AC-PROJ-023.3 (a `.change.yaml` with no record loads), tagged `@ac`; verify they fail on the stubs
- [x] 1.3 [code] Implement `dirty_files`, `Change.dirty` (saved and loaded) and the record in `set_phase` and `create_change` (REQ-PROJ-023), tagged `@req`; verify `specworks run lint` passes and, in a scratch repository with a dirty file, `specworks phase design` on a sample change writes a `dirty:` list in its `.change.yaml`
- [x] 1.4 [test] Review R1, R2 and R3: a test for AC-PROJ-023.4 (a move outside a git repository succeeds with no record); the AC-PROJ-023.1 test checks that a move without `root` leaves the record as it was instead of an empty record (R1); tests for a workspace in a subfolder of the repo and for a staged `git mv`, paths relative to the workspace root (R3), tagged `@ac`; verify the AC-PROJ-023.4 test fails before 1.5
- [x] 1.5 [code] Review R2: outside a git repository, `set_phase` and `create_change` move the change with no record (REQ-PROJ-023), tagged `@req`; verify `specworks run lint` passes and, in a scratch folder with no `.git`, `specworks phase design` on a sample change moves it

## 2. Committing a phase

- [x] 2.1 [test] Tests for AC-PROJ-024.1 to AC-PROJ-024.5 (only the phase's files; already dirty and changed again; the message with trailers and a given subject; nothing to commit; detached HEAD), in a temporary git repository, asserting the pinned wording of design.md, tagged `@ac`; verify they fail on the stubs
- [x] 2.2 [code] Implement `commit` in `git.py` and `commit_phase` in `changes.py` as design.md decides, with its pinned wording (REQ-PROJ-024), tagged `@req`; verify `specworks run lint` passes and, in a scratch repository, a phase commit holds only the files changed since the phase started

## 3. The command and the skills

- [x] 3.1 [test] Tests for AC-CLI-012.1 (a commit with `--trailer` and `--json`: the fields, relative paths, and `git log` showing the subject and trailer), AC-CLI-012.2 (nothing to commit: `commit` null) and AC-CLI-012.3 (an unknown change: an error naming it, exit 1), tagged `@ac`; and a wording check that `_shared/committing.md` has the pinned skill text; verify they fail on the stubs
- [x] 3.2 [code] Add `specworks commit` in `src/specworks/cli/changes.py`, pass the workspace root from `new`, `phase` and `start` (REQ-CLI-012, REQ-PROJ-023), and rewrite `src/specworks/skills/_shared/committing.md` with the pinned skill text; refresh the installed copies with `uv run specworks skills`; verify `specworks run lint` passes and `specworks commit --help` shows `--message` and `--trailer`
