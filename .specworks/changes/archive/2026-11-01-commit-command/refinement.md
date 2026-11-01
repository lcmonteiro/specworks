# Refinement: commit-command

## Problem

At the end of each phase, the agent commits the phase's work by hand: seven
skills (through `_shared/committing.md`) tell it to stage only the change
folder and the files the phase wrote, to leave out and name any unrelated
dirty file, and to write `<ref>: <phase>` or the project's convention. The
agent decides which files belong to the phase from `git status` and memory,
and builds the `git add … && git commit …` command itself. It is slow (about
40 hand-built commits in the last builds), it can let unrelated work in or
leave a phase file out, and it differs from skill to skill. The user wants
the process as safe, deterministic and fast as possible. (Source: user
request in session, paraphrased; item 4 of the sequence in
`deterministic-steps`.)

## Outcomes

- When a phase starts (`specworks new`, `specworks start`, `specworks
  phase`), the change's `.change.yaml` records which files are already dirty
  or untracked, with a hash of their content.
- `specworks commit --change <ref>` stages the change folder plus every file
  that became dirty, or changed again, since that record; it stages nothing
  else, never with `git add -A`, and lists the dirty files it left out, and
  why.
- The message is `<ref>: <phase>`; `--message` replaces the subject and
  `--trailer "Key: value"` (repeatable) adds trailers, such as
  `Co-Authored-By` or the project's convention.
- When there is nothing new to commit, it says so and creates no commit.
- It never pushes.
- `--json` returns the commit, the files committed and the files left out;
  errors are values, as in every command.
- `_shared/committing.md` (and through it the 7 skills) uses `specworks
  commit` instead of hand-built git commands.

## Context

**Observed:**
- `src/specworks/skills/_shared/committing.md` holds the commit rules; 7
  skills include it.
- `src/specworks/core/git.py` runs git (`git`, `git_text`, `require_repo`)
  and creates a change's branch (REQ-PROJ-017/018/019); nothing commits.
- `src/specworks/core/changes.py` `set_phase` writes the phase to
  `.change.yaml`; `specworks start` and `specworks phase` go through it,
  `specworks new` writes the file first.
- In the last builds, a code half whose gate failed did not commit, and the
  coordinator chose its files by hand.

**Assumed:**
- A file that was already dirty before the phase and that the phase changed
  again goes into the commit whole, flagged ("was already dirty before the
  phase"); its two sets of edits cannot be told apart.

## Constraints

- [hard] Only the change folder and the phase's files are staged; never
  `git add -A`; a file the user was editing that the phase did not touch is
  never committed.
- [hard] It never pushes, never rewrites history, and refuses a detached
  HEAD.
- [hard] It works the same in a test half's worktree as in the main
  checkout.
- [soft] It works from the record alone: no hidden git refs, nothing outside
  `.specworks/`.

## Options

### Option A: Paths and hashes in `.change.yaml`

Each phase move records the dirty and untracked files (staged, unstaged and
new) with a content hash; `commit` compares the current dirty files with
that list.

- **Pros:** deterministic, readable, testable, kept with the change.
- **Cons:** a file dirty before and during the phase cannot be split.
- **Effort:** M
- **Touches:** `project`, `cli`
- **Outcomes:** meets all seven.

### Option B: A hidden git ref

Each phase move saves the working tree as a temporary commit
(`git stash create`) under `refs/specworks/<ref>`; `commit` diffs against it.

- **Pros:** exact to the line.
- **Cons:** refs outside the files, to clean up and keep in step across
  worktrees.
- **Effort:** M-L
- **Touches:** `project`, `cli`
- **Outcomes:** meets all seven; fails the soft constraint.

### Option C: Modification times

The files modified after the phase move.

- **Pros:** nothing to record.
- **Cons:** checkout, editors and worktrees change mtimes; not deterministic.
- **Effort:** S
- **Touches:** `project`, `cli`
- **Outcomes:** fails the point of the change.

## Recommendation

Option A, agreed with the user: deterministic and readable, kept with the
change.

## Open Questions

- The rest of the sequence from `deterministic-steps` (`config set`,
  `capability add --create`, an option for `new` not to switch branch,
  shared rule text) stays for later changes. Not blocking. (who can answer:
  maintainer)

## Candidate Capabilities

- `project`: modified - the dirty-file record at each phase move, and the
  commit of a phase
- `cli`: modified - the `specworks commit` command
