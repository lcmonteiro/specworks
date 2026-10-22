# Tasks: git-workflow

## 1. The git repository and a change's branch

- [x] 1.1 Add `GitMissing`, `Branch`, `require_repo`, `branch_name`, `plan_branch` and `create_branch` to `src/specworks/core/git.py` as stubs (REQ-PROJ-017, REQ-PROJ-018, REQ-PROJ-019); verify `uv run mypy` and the existing tests pass
- [ ] 1.2 [test] Write failing tests in `tests/test_git.py` for AC-PROJ-017.1, AC-PROJ-017.2, AC-PROJ-017.3, AC-PROJ-018.1, AC-PROJ-018.2, AC-PROJ-018.3, AC-PROJ-019.1, AC-PROJ-019.2, AC-PROJ-019.3 and AC-PROJ-019.4, each tagged `@ac`; verify they fail for the right reason
- [ ] 1.3 [code] Implement `GitMissing` and `require_repo` (REQ-PROJ-017) tagged `@req`; verify `uv run pytest tests/test_git.py`
- [ ] 1.4 [code] Implement `branch_name`, `plan_branch` and `create_branch` (REQ-PROJ-018, REQ-PROJ-019) tagged `@req`; verify `uv run pytest tests/test_git.py`

## 2. `init` and `new`

- [x] 2.1 Add the `--no-branch` option to `new` in `src/specworks/cli/changes.py` as a stub (REQ-CLI-006); verify `uv run mypy` and the existing tests pass
- [ ] 2.2 [test] Write failing tests for AC-CLI-003.7, AC-CLI-006.6, AC-CLI-006.7, AC-CLI-006.8 and AC-CLI-006.9 in `tests/test_cli.py`, tagged `@ac`, and add the repo to AC-CLI-003.1's test; verify they fail for the right reason
- [ ] 2.3 [code] Make `init` refuse a folder outside a git repository before writing anything (REQ-CLI-003, AC-CLI-003.7) tagged `@req`; verify the `init` tests
- [ ] 2.4 [code] Make `new` plan the branch, create the change, switch to the branch, and report `branch` and `startedFrom` (REQ-CLI-006, AC-CLI-006.6 to AC-CLI-006.9) tagged `@req`; verify the `new` tests

## 3. Sample projects in a repo

- [ ] 3.1 [test] Put every sample project of the tests in a git repo: `git init` in `tests/helpers.py` and the fixtures of `tests/test_cli.py`, `tests/test_diagrams.py`, `tests/test_modules.py`, `tests/test_skills.py`, `tests/test_walkthrough.py` and `tests/test_propose.py`; `new --no-branch` in the planned project so it stays on `main`; delete `.git` in the tests of behaviour without git; verify `uv run pytest` passes once the code is done (REQ-CLI-003, REQ-CLI-006)

## 4. Skills

- [ ] 4.1 [code] Write `src/specworks/skills/_shared/committing.md` and `src/specworks/skills/_shared/pushing.md` as in design.md, include them in the phase skills and in `specworks-close` and `specworks-done`, update `specworks-baseline`, `specworks-build` and the `allowed-tools` of the skills that commit, then run `uv run specworks skills`; verify the installed copies show the shared text
- [ ] 4.2 [test] Update `tests/test_skills.py`: the allow-list test accepts `git add` and `git commit` and rejects `git push`; add tests that each committing phase skill has `**Committing**`, that no skill says `git add -A`, and that close and done ask before pushing; verify `uv run pytest tests/test_skills.py`

## Workflow follow-up

- Update the wiki pages that describe `init`, `new` and the skills, and the commit rule in `CLAUDE.md`, once the change is closed.
