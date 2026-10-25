# Proposal: git-workflow

## Why

Git is only advice in the skills: nothing makes a repo a precondition, puts a change on its own branch, records each step or ends at a PR. Review and the run cache already rely on git, and a branch per change gives review a real base. Refinement: option B (CLI for the mechanical parts, skills for commits, push and the PR link).

## What Changes

- `init` refuses a folder that is not inside a git repository, before writing anything. It never runs `git init`. **BREAKING** for scripts that ran `init` outside a repo.
- `new` creates and switches to the change's branch, named after its ref (`<name>`, `<module>/<name>` in a module), starting from the current HEAD. `--no-branch` stays on the current branch. **BREAKING**: `new` fails outside a git repository.
- `new` refuses an existing branch of that name or a detached HEAD, and leaves nothing behind. It says when it started from a branch other than the base branch.
- Skill text: each phase skill ends with a commit after its gate passes (explicit paths, unrelated files left out; the project's commit convention first, else `<ref>: <phase>`), and `/specworks-close` and `/specworks-done` ask before pushing and relay the remote's PR link (fallback: derived for `github.com` and `gitlab.com`). Skill wording has no capability yet, so it carries no requirements.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: new requirements for the git repository a project lives in (REQ-PROJ-017), a change's branch name (REQ-PROJ-018) and where that branch starts (REQ-PROJ-019).
- `cli`: REQ-CLI-003 `init` (refuses outside a repo) and REQ-CLI-006 `new` (creates the branch, `--no-branch`, refusals, the base-branch note).

## Impact

- Code: `core/git.py` (repository check, branch name, create the branch), `cli/project.py` (`init`), `cli/changes.py` (`new`), `core/changes.py` or the CLI for the order of checks.
- Skills (`src/specworks/skills/`, then `specworks skills`): the phase skills, `_shared`, `specworks-baseline` (the "preferably on a new branch" step), `specworks-close`, `specworks-done`. `tests/test_skills.py` checks some wording.
- Tests: `tests/helpers.py` and `tests/conftest.py` must put sample projects in a git repo; `init`/`new` tests change.
- Wiki and the `CLAUDE.md` commit rule follow once the change is closed.

## Out of Scope

- Commits, push and the PR link in the CLI: they stay in the skills.
- A branch-name prefix or other git settings in `spec.yml`.
- Changing review's base detection or the "on the base branch" fallback (AC-FLOW-009.5, AC-FLOW-011.5).
- Special handling of git-submodule modules: the repo is whichever git reports for the folder.
- Creating pull requests through a forge CLI or API.
- Assumptions: unrelated dirty files stay out of commits; `new` on a dirty tree carries the changes over to the new branch.
