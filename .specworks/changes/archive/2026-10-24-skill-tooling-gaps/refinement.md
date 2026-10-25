# Refinement: skill-tooling-gaps

## Problem

The last builds (`phase-subagents`, `parallel-test-code`,
`fix-no-own-tests-gate`) showed four gaps in the skill text and tooling. They
make the build flow lean on the subagent working things out, or spend a run
on nothing. None changes the CLI's behaviour. The fifth gap found then
(validate naming `/specworks-code` for a `[test]` task) is a behaviour bug
and goes to its own change, `fix-validate-test-task-skill`.

## Context

**Observed:**
- `src/specworks/skills/_shared/phase-subagents.md` expects design to write
  `## Interfaces` with the line `Proposed: waiting for the user's agreement`,
  which the coordinator replaces with `Agreed with the user`. The design skill
  (`specworks-design/SKILL.md`, steps 3-4) never mentions either line.
- `specworks-build/SKILL.md` step 2 says "the worktree starts from HEAD". In
  `fix-no-own-tests-gate`, the test half's worktree started from an older
  commit, without design's stubs, and the subagent fast-forwarded it itself.
- `specworks-build/SKILL.md` step 3: after the user decides the findings, a
  fresh review subagent always runs to tick done findings and gate the
  review, even when every finding was decided `accepted` and nothing is left
  to change.
- `.gitignore` does not list `.claude/worktrees/`, so worktrees show as
  untracked (kept out only by a local `.git/info/exclude`).

**Assumed:**
- The first entry of `git worktree list` is the main checkout, whose HEAD
  holds design's committed stubs.

## Constraints

- [hard] No behaviour change: the change is marked `specworks skip-specs`,
  so it has no delta specs and no `@ac` tags.
- [hard] Skills are edited in `src/specworks/skills/` only, then
  `uv run specworks skills` refreshes the installed copies, committed
  together; `tests/test_skills.py` wording checks keep passing (updated where
  the wording moves).
- [hard] The subagent prompt in `phase-subagents.md` stays fixed: no extra
  text per run.

## Options

### Option A: Fix the four gaps in the skill text and `.gitignore`

- Design skill: when it stops to agree on the API, it writes `## Interfaces`
  with `Proposed: waiting for the user's agreement`; it creates the stubs
  only once that line reads `Agreed with the user` (or the user agreed in
  the same conversation).
- Test skill: in a worktree, before writing tests, fast-forward to the main
  checkout's HEAD (`git worktree list`, then `git merge --ff-only`). Build
  skill: drop "the worktree starts from HEAD" and point to that check.
- Build skill: skip the finishing review subagent when every finding is
  decided `accepted` and no finding from an earlier cycle needs ticking;
  the coordinator runs `specworks gate review --change <ref> --allow-open`
  itself.
- `.gitignore`: add `.claude/worktrees/`.

- **Pros:** closes every gap the builds hit; small text edits.
- **Cons:** the coordinator gains one shortcut to remember.
- **Effort:** S
- **Touches:** skills (no capability), repo tooling

### Option B: Do nothing

- **Pros:** no work.
- **Cons:** each build repeats the workarounds; the `Proposed:` contract
  stays one-sided.
- **Effort:** -
- **Touches:** -

## Recommendation

Option A, as agreed with the user, with the review finish run skipped when
nothing is left to do (the user's choice over always running it).

## Open Questions

None.

## Candidate Capabilities

- None: skill text and tooling only (`skip-specs`). The validate fix is
  `fix-validate-test-task-skill`, a later change in `workflow`.
