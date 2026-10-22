# Refinement: git-workflow

## Problem

A change produces a lot of work (refinement, specs, stubs, tests, code, review, living docs), but git is only advice in the skills' prose. Nothing makes a repo a precondition, isolates a change on its own branch, records each step, or ends at a PR. The user asked: "on specworks init git is precondition", "when we start a change we should create a branch and work on this branch", "commit to each step", and "in the end we can suggest a push and a link to PR if applicable". Also: "if the project has a skill to commit format msg adapt to it".

## Context

**Observed:**
- `core/git.py` only reads git: `git`, `git_text`, `GitError`. Callers: `core/runner.py` (the run cache lives in `.git/`, reuse is off without git) and `workflow/review.py` (base branch from `origin/HEAD`, `merge-base`, changed files).
- `cli/project.py` `init` checks no repo. It already rejects a bad `--tools` before writing anything. `cli/changes.py` `new` only creates the folder.
- `review_change` falls back to `change_start` (the commit that added the change's metadata) when HEAD is on the base branch (AC-FLOW-009.5); a branch per change makes that fallback rare.
- Skills: `specworks-baseline` says "preferably on a new branch"; `specworks-build` commits design before the parallel halves and merges the test half's worktree branch; `specworks-close` only suggests `git add -A && git commit -m "<change>: close"` and "opening the PR if the project uses them".
- Tests build sample projects in plain tmp folders (`tests/helpers.py`); only `make_repo` and `test_walkthrough.py` create repos.
- This repo's `origin` uses an ssh alias (`git@github-lcmonteiro:...`), so the forge cannot be told from the URL. GitHub and GitLab print the "create a pull request" link in the push reply.
- Skills are installed for Claude Code (`.claude/skills/`) and Copilot (`.github/skills/`); a project's own commit-message skill or convention can live in either, in `CLAUDE.md`, in `.github/copilot-instructions.md` or in `spec.yml` `context`.

**Assumed:**
- A branch name from the ref never collides with a project's own `feature/` conventions in a way that matters.
- `git switch -c` carries uncommitted changes, so `new` on a dirty tree is safe.
- Modules inside the parent's repo share it; a git submodule used as a module has its own repo, and the change's branch lives there.

## Constraints

- [hard] `init` and `new` must not leave half-written files when git is missing.
- [hard] Pushing is never done without the user's yes.
- [hard] A project's commit-message convention takes precedence over specworks' default.
- [hard] Stdlib and `core/git.py` only: no `gh` or forge CLI is required.
- [hard] Existing behaviour: reads of git stay as they are; non-ASCII names, Windows and CI keep working (`encoding="utf-8"`).
- [soft] Unrelated dirty or untracked files (e.g. `.vscode/`) stay out of a change's commits.
- [soft] Phase commits only after the phase's gate passes.

## Options

### Option A: Skills only

The CLI stays read-only. Branch, commit, push and PR link are prose in the skills.

- **Pros:** no CLI or spec change; follows any commit convention naturally.
- **Cons:** the precondition and the branch are not enforced or tested; behaviour varies by agent; `init` still accepts a folder with no repo.
- **Effort:** S
- **Touches:** none (skills only)

### Option B: CLI for the mechanical parts, skills for the rest

- `init` fails with a hint when the folder is not in a git repo and writes nothing.
- `new` creates and switches to a plain branch (`<name>`, or `<module>/<name>` for a module change) from the current HEAD, notes when HEAD is not the base branch, refuses an existing branch or a detached HEAD; `--no-branch` stays on the current branch.
- Skills commit at the end of each phase after its gate passes, staging explicit paths and leaving unrelated files out; the message follows the project's convention, otherwise `<ref>: <phase>`.
- At the end (`/specworks-close`, `/specworks-done`) the skill asks before pushing, then relays the PR link the remote prints; when none is printed it derives one for `github.com` and `gitlab.com` origins.

- **Pros:** the deterministic parts (precondition, branch naming, edge cases) are tested; the parts that need judgment (message convention, staging, consent) stay with the agent.
- **Cons:** `init`/`new` get stricter, so old projects without git need a clear error; test fixtures need a repo; the skill text grows.
- **Effort:** M
- **Touches:** `project`, `cli`, skills (`integrations`)

### Option C: CLI does everything

`new` branches, `start` auto-commits the phase it leaves, and a command prints the PR link.

- **Pros:** most automatic; same behaviour for every agent.
- **Cons:** cannot honour a project's commit convention without a template or flag; commits happen inside parallel halves and worktrees, which clash with `/specworks-build`; the forge cannot be told from an ssh alias.
- **Effort:** L
- **Touches:** `project`, `workflow`, `cli`

## Recommendation

Option B, agreed with the user. Decisions taken: plain branch names; branch from the current HEAD with a note; commits stage explicit paths after the gate passes; `init` fails with a hint and never runs `git init`; ask before pushing, then relay the remote's PR link (fallback: derive for `github.com`/`gitlab.com`).

## Open Questions

- How do skills detect a project's commit convention (a commit skill, `CLAUDE.md`, `context`)? Proposed: skill text says to follow it if one exists, else `<ref>: <phase>`; the change ref and phase go in the body or a trailer when the convention allows. (who can answer: user, at specify)
- How does the per-phase commit interact with the parallel test worktree in `/specworks-build`? (who can answer: design, from the build skill)
- Should `new` in an old project without git fail, or warn and skip the branch? (who can answer: user, at specify)
- Does a git-submodule module branch inside the submodule's repo? (who can answer: design)

## Candidate Capabilities

- `project`: modified - the git precondition in the workspace and `core/git.py` writing (branch creation).
- `cli`: modified - `init` fails outside a repo; `new` creates the branch and `--no-branch`.
- `integrations`: modified - the installed skills commit per phase and end with a push and a PR link.
- `workflow`: modified, maybe - review's base detection and "On the base branch" fallback once every change has a branch.
