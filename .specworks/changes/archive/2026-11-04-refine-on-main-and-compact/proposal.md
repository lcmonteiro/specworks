# Proposal: refine-on-main-and-compact

## Why

`/specworks-refine` starts a change in whatever state the session is in:
`specworks new` branches from the checked-out branch and only notes
`started from <branch>` afterwards, so a change started from another change's
branch is silently stacked on it, and the long exploratory phase begins in a
conversation that already holds earlier work (see refinement.md, Option A).

## What Changes

- `specworks-refine` gets a section `## Before step 1` with two ordered
  stops, both before the skill reads or runs anything:
  1. **Clear context**: when the conversation already holds earlier work
     (anything before the request except a summary left by `/compact`), ask
     `Compact the conversation first? (yes/no)`. On yes, tell the user to run
     `/compact` and `/specworks-refine` again with the same request, and stop
     (a skill cannot compact the conversation itself). A new or
     just-compacted conversation goes straight on.
  2. **Base branch**: run `git status --short --branch`; when the checked-out
     branch is not the base branch (`main`, or `master` when the repository
     has no `main`), ask `You are on <branch>, not <base>. Switch to <base>?
     (yes/no)`. On yes, run `git switch <base>`; on no, stay (a change
     continued on its own branch, or a deliberately stacked one). When the
     working tree has changes, say so, stay and ask nothing.
- `tests/test_skills.py`: wording tests for both stops, their order, and that
  no other skill carries them.
- `docs/architecture.md`: one decision, "Refine starts clear and from the base
  branch".
- Installed skill copies refreshed with `uv run specworks skills`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- None: skill text, tests and docs only; `skills/` has no capability yet.
  Marked `specworks skip-specs`.

## Related requirements

- REQ-PROJ-018 left: the change's branch is still created by `new`; the skill only asks first.
- REQ-PROJ-019 left: the branch still starts at the current HEAD and reports `startedFrom`.
- REQ-PROJ-026 left: `branch_per_change` is unchanged; the base-branch question is asked either way.
- REQ-CLI-006 left: `new`'s output and options are unchanged.

## Impact

- `src/specworks/skills/specworks-refine/SKILL.md`
- `tests/test_skills.py`, `docs/architecture.md`
- Installed copies under `.claude/skills/`
- No CLI, config, schema or data change; `allowed-tools` is unchanged (`git
  switch` is never pre-approved, so the user is asked to approve it).

## Out of Scope

- The other phase skills (specify, build, done, ...): they run mid-change,
  where switching to `main` is wrong, and an existing conversation is theirs.
- A CLI check or warning on `new` (it already reports `startedFrom`).
- Offering `git pull` after the switch.
- Judging "earlier work" with a CLI signal: the agent reads its own
  conversation.
