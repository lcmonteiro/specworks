# Proposal: skill-tooling-gaps

## Why

The last builds showed four gaps in the skill text and tooling that make the
build flow rely on a subagent's workaround, or spend a run on nothing. The
refinement chose Option A: close all four in the skill text and
`.gitignore`, with no behaviour change.

## What Changes

- `specworks-design`: when it stops to agree on the API, it writes
  `## Interfaces` with the line `Proposed: waiting for the user's agreement`
  first; it creates the stubs only once that line reads
  `Agreed with the user`, or the user agreed in the same conversation. This
  matches the contract in `_shared/phase-subagents.md`.
- `specworks-test`: in a git worktree, before writing tests, it fast-forwards
  to the main checkout's HEAD (the first entry of `git worktree list`, then
  `git merge --ff-only <commit>`), so it holds design's stubs; if that is not
  a fast-forward, it returns `blocked`.
- `specworks-build`: drops "the worktree starts from HEAD" and points to the
  test skill's check. After the user decides the review findings, when every
  finding is decided `accepted` and no finding from an earlier cycle needs
  ticking, the coordinator runs
  `specworks gate review --change <ref> --allow-open` itself instead of
  starting a fresh review subagent.
- `.gitignore`: add `.claude/worktrees/`.
- Wording checks in `tests/test_skills.py`, and the installed copies
  refreshed with `specworks skills`.

## Capabilities

None: only packaged skill text and repo tooling change, and no capability
holds requirements for the skills. The change is marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- `src/specworks/skills/specworks-design/SKILL.md`,
  `src/specworks/skills/specworks-test/SKILL.md`,
  `src/specworks/skills/specworks-build/SKILL.md`, `.gitignore`,
  `tests/test_skills.py`, and the installed copies (`.claude/skills/`,
  `.github/skills/`, `.github/prompts/`).
- No CLI, API or data change.

## Out of Scope

- Validate naming `/specworks-code` for an open `[test]` task: a behaviour
  bug in `workflow`, done next as `fix-validate-test-task-skill`.
- Changing the fixed subagent prompt in `_shared/phase-subagents.md`.
