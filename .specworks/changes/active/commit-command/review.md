# Review: commit-command

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **test-gap** AC-PROJ-023.1: the test fails on its first assertion. It expects a fresh change to have an empty record after a move without `root` (`assert change(project).dirty == {}`), but `specworks new` in the fixture records `.specworks/config.yml` (untracked when the change is created), as REQ-PROJ-023 requires; the criterion says nothing about the record at creation (`tests/test_commit.py:93`)
  - **Proposal**: back to test: assert that a move without `root` leaves the record as it was (take it before `set_phase(ch, "specify")` and compare), instead of asserting it is empty
  - **Decision**: back to test: check that a phase move without root leaves the record as it was, instead of checking that a new change's record is empty (agreed with the user)
- [ ] R2 **spec-gap** REQ-PROJ-023 is silent on a workspace outside a git repository, and the agreed `dirty_files` raises `GitError` there, so `specworks phase` and `specworks start` now fail outside git with `fatal: not a git repository ...`, where they moved the change before (REQ-PROJ-011 lets a change move to any phase; review and the gates already work without git, AC-FLOW-009.4) (`src/specworks/core/changes.py:173`, `src/specworks/workflow/gate.py:242`)
  - **Proposal**: back to specify: MODIFIED REQ-PROJ-023 adds "Outside a git repository the move SHALL still succeed, with no record", with a scenario AC-PROJ-023.4; then the test half tests it and the code half records nothing when `dirty_files` raises `GitError`
  - **Decision**: back to specify: REQ-PROJ-023 says that outside a git repository a phase move still succeeds with no record, with scenario AC-PROJ-023.4; then the test and code halves follow (agreed with the user)
  - done in specify: added to REQ-PROJ-023 that outside a git repository the move succeeds with no record, scenario AC-PROJ-023.4, and tasks 1.4 [test] and 1.5 [code]
  - done in design: design.md records that set_phase and create_change catch GitError outside a git repository and move or create the change with an empty record; dirty_files keeps raising; no signature changes, so no new stubs
- [ ] R3 **test-gap** AC-PROJ-023.1 / AC-CLI-012.1 check paths "relative to the workspace root" only where the workspace root is the git root, so they would still pass if `dirty_files` stopped stripping the `rev-parse --show-prefix` prefix (the case design.md Context calls out); a staged rename (both paths recorded) is untested too. `src/specworks/core/git.py` is at 90% branch coverage (lines 136-143) (`tests/test_commit.py:101`)
  - **Proposal**: back to test: add a test under AC-PROJ-023.1 with the workspace in a subfolder of the repository, a dirty file outside it and one inside, asserting the record names only the inside one by its workspace-relative path; and one with a staged `git mv` asserting both paths are recorded
  - **Decision**: back to test: add a test with the workspace in a subfolder of the repo, and one with a staged git mv (agreed with the user)

## Changed files without tags

None: `specworks review` lists no untraced source or test file. The other
changed files are not scanned for tags: `src/specworks/skills/_shared/committing.md`
and the seven installed `.claude/skills/*/SKILL.md` copies (skill text, checked
verbatim by `tests/test_skills.py::test_the_shared_committing_text_commits_with_specworks_commit`).

## Summary

The code matches REQ-PROJ-023, REQ-PROJ-024, REQ-CLI-012 and design.md's
Interfaces and pinned wording (checked by hand too: a workspace below the git
root, a deletion-only commit and a staged rename commit correctly). Three open
findings, nothing fixed here (inside /specworks-build): one failing test that
asserts beyond its criterion (R1, test), phase moves that now fail outside git
(R2, specify) and untested workspace-relative and rename paths (R3, test).
