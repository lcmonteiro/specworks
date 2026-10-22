# Design: git-workflow

## Context

See [proposal.md](proposal.md) for the motivation and [refinement.md](refinement.md) for the options. Git is read today by `core/runner.py` (the run cache) and `workflow/review.py` (base branch, changed files) through `core/git.py` (`git`, `git_text`, `GitError`). `init` and `new` never touch it. Layering is `core` → `specs` → `workflow` → `cli`, so `core/git.py` cannot call `detect_base`, which lives in `workflow/review.py`.

## Goals / Non-Goals

**Goals:**
- `init` and `new` require a repo; `new` puts the change on its branch, with nothing left behind on a refusal.
- The phase skills commit after their gate passes; the closing skills ask before a push and relay the PR link.

**Non-Goals:**
- Commits, push or PR links in the CLI.
- A config key for the branch name or the commit message.
- Moving `detect_base`, or changing review's base logic.

## Decisions

### The CLI plans, then changes the repo (REQ-PROJ-018, REQ-PROJ-019, REQ-CLI-006)

`new` first checks everything that can refuse (repo, detached HEAD, existing branch), then creates the change folder, then creates and switches to the branch. A refusal therefore leaves no folder and no branch (AC-CLI-006.8); a bad or used change name fails in `create_change` before the repo is touched. `plan_branch` has no side effects, `create_branch` is the only writer. Alternative: create the branch first and roll back on error: more states to undo.

### Branch from `git checkout -b` (REQ-PROJ-019)

`git switch -c` needs git 2.23; `checkout -b` works everywhere, carries uncommitted changes, and works on a repository without commits.

### The base branch is passed in, not found in core (REQ-PROJ-019)

`plan_branch(cwd, name, base)` takes the base branch name; the CLI finds it with `detect_base` and passes `None` when it cannot be found (`GitError`). A base of `origin/main` counts as the current branch `main`. Alternative: move `detect_base` into `core/git.py`: touches workflow code and its tests for no behaviour gain.

### `not installed` is its own error (REQ-PROJ-017)

`GitMissing(GitError)` is raised by `git()` when the program cannot be run; every existing `except GitError` keeps working. `require_repo` re-raises it as is, and turns any other failure of `git rev-parse` into "not inside a git repository: run `git init` first". `init` may be given a folder that does not exist yet, so `require_repo` runs git from the nearest existing parent.

### `--no-branch` still needs a repo (REQ-CLI-006)

Git is a precondition of the project, not of the branch: `new --no-branch` outside a repo fails the same way.

### Skills commit, the CLI does not (no requirement: skill text has no capability)

- `src/specworks/skills/_shared/committing.md`, included by refine, specify, design, test, code, review and close as `**Committing**`: after the phase's gate passes and before the closing question; stage explicit paths (the change folder and the files the phase wrote or changed, never `git add -A`); name unrelated dirty or untracked files in the report and leave them out; the message follows the project's commit convention when one exists (a commit skill, `CLAUDE.md`, `.github/copilot-instructions.md`, the `context`), otherwise `<ref>: <phase>`, with the ref and phase in the body or a trailer when the convention allows; never push. validate is read-only and does not commit.
- `src/specworks/skills/_shared/pushing.md`, included by close and done: ask `Push <branch>? (yes/no)`; on yes run `git push -u origin <branch>` and relay the "create a pull request" link the remote prints; when it prints none and `origin` is a `github.com` or `gitlab.com` URL, build `/pull/new/<branch>` or `/-/merge_requests/new?merge_request[source_branch]=<branch>`; otherwise only report the push.
- Frontmatter `allowed-tools` of those skills gains `Bash(git add:*)` and `Bash(git commit:*)`. `git push` is never pre-approved: the user is asked either way.
- `specworks-baseline` drops "preferably on a new branch": `new` makes the branch. `specworks-close` drops the `git add -A && git commit` suggestion. `specworks-build` no longer says to commit design's work itself: the design skill does.
- In a build, the test half commits on its worktree branch (the skill already says so) and the code half in the main checkout; the merge and its `tasks.md` rule are unchanged.

## Interfaces

Agreed with the user

- `src/specworks/core/git.py`:
  - `class GitMissing(GitError)`: git cannot be run (REQ-PROJ-017).
  - `require_repo(path: Path) -> None`: raises `GitMissing` or `GitError` ("not inside a git repository: run `git init` first") (REQ-PROJ-017).
  - `branch_name(ref: str) -> str`: `ref` with `:` replaced by `/` (REQ-PROJ-018).
  - `@dataclass(frozen=True) class Branch`: `name: str`, `started_from: str | None` (REQ-PROJ-019).
  - `plan_branch(cwd: Path, name: str, base: str | None = None) -> Branch`: no side effects; raises `GitError` for an existing branch or a detached HEAD (REQ-PROJ-018, REQ-PROJ-019).
  - `create_branch(cwd: Path, branch: Branch) -> None`: creates and switches to the branch, carrying the working tree over (REQ-PROJ-018, REQ-PROJ-019).
- `src/specworks/cli/project.py`: `init` calls `require_repo` after `parse_tools` and before writing anything (REQ-CLI-003).
- `src/specworks/cli/changes.py`: `new(name, module, no_branch: bool, as_json)`: option `--no-branch`; text output adds `branch <name>` and, when set, `started from <branch>`; `--json` adds `branch` (`str | None`) and `startedFrom` (`str | None`) (REQ-CLI-006).
- Skills: `src/specworks/skills/_shared/committing.md`, `src/specworks/skills/_shared/pushing.md` as above.

## Risks / Trade-offs

- [Every sample project in the tests now needs a repo] -> `tests/helpers.py` and the other fixtures run `git init` in the project folder and create changes with `new --no-branch`, so the tests keep working on `main`. The tests of "no git" behaviour (review without git, the run cache without git) delete the `.git` folder.
- [Existing projects without a repo cannot start a change] -> the error says `git init`; one command fixes it.
- [`git add` of explicit paths depends on the agent following the skill] -> the skill text says so and a test pins its wording; the run cache and review already ignore commits.
- [A project's commit skill is found only by the agent] -> the skill text lists where to look; with none, the default message is used.

## Migration / Rollback

None for data. Existing projects run `git init` once. Rollback is reverting the change.

## Open Questions

- None.
