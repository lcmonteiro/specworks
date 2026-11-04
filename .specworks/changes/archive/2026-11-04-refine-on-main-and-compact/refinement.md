# Refinement: refine-on-main-and-compact

## Problem

`/specworks-refine` starts a change in whatever state the session is in. `specworks new` creates the change's branch from the checked-out branch and only notes `started from <branch>, not the base branch` afterwards, which the skill never relays, so a change started from another change's branch is silently stacked on it. Refine is also the longest, most exploratory phase, and it begins in whatever conversation is already open, with earlier work cluttering the context.

## Outcomes

- On a branch other than `main`, refine asks `Switch to main? (yes/no)` before it creates the change. On yes it switches to `main`; with a dirty working tree it says so and stays. On `main` it says nothing.
- When the conversation already holds earlier work, refine asks `Compact the conversation first? (yes/no)` before it reads or runs anything. On yes it stops and tells the user to run `/compact` and re-run `/specworks-refine` with the same request. A fresh or just-compacted session starts straight away.
- The compact prompt comes first, then the main-branch check, then the existing step 1.

## Context

**Observed:**
- `specworks new` creates and checks out the change's branch from HEAD; off the base branch it reports `startedFrom` (REQ-PROJ-018/019, AC-CLI-006.6 and AC-CLI-006.9 in `src/specworks/cli/docs/spec.md`). It never switches branch itself.
- The base branch candidates are `origin/main`, `main`, `origin/master`, `master` (`BASE_CANDIDATES` in `src/specworks/workflow/review.py`).
- `src/specworks/skills/specworks-refine/SKILL.md` starts at step 1 (`specworks context --json`); no skill mentions switching branches or compacting.
- A skill cannot run `/compact`: it can only ask the user to.
- `tests/test_skills.py` checks skill wording verbatim.
- Stacked changes are legitimate (`--base <branch>` on the gates exists for them).

**Assumed:**
- The agent can tell whether the conversation holds earlier work, including a compaction summary at its start.
- The base branch is `main` for this project; other projects may use `master`.

## Constraints

- [hard] Skill text only: edit `src/specworks/skills/specworks-refine/SKILL.md`, then run `specworks skills` to refresh the installed copies. The change is `skip-specs`.
- [hard] Every stop ends with one closing question (yes/no or numbered options), per `_shared/asking-the-user.md`.
- [hard] Never switch branches with a dirty working tree.
- [soft] Never force `main`: a deliberately stacked change must stay possible.
- [soft] The other phase skills stay unchanged.

## Options

### Option A: Two ordered stops in the refine skill

Before step 1, refine asks about compacting (only when the conversation holds earlier work), then, when not on the base branch, asks whether to switch to it.

- **Pros:** the compaction happens before any work, a stacked change stays possible, no CLI change.
- **Cons:** up to two extra turns at the start; "earlier work" is a judgement call.
- **Effort:** S
- **Touches:** none (skill text and `tests/test_skills.py`)
- **Outcomes:** meets all three.

### Option B: Non-blocking notes only

Refine prints `On <branch>, not main` and `Tip: run /compact` at the top and goes on without asking.

- **Pros:** no extra turns.
- **Cons:** easy to ignore, so the stacked change and the cluttered context remain.
- **Effort:** S
- **Touches:** none
- **Outcomes:** meets none reliably.

### Option C: Always ask, in every phase skill

A shared text with both prompts, included in every phase skill.

- **Pros:** one rule everywhere.
- **Cons:** about 12 skills and their wording tests change; later phases run mid-change, where switching to `main` is wrong.
- **Effort:** M
- **Touches:** none
- **Outcomes:** meets all three for refine, but over-reaches elsewhere.

## Recommendation

Option A: both prompts live in the refine skill, compact first and the branch check second. The user chose to compact at the start of refine and only when the conversation holds earlier work, which avoids a loop after `/compact`.

## Open Questions

- How should "earlier work" be judged in a fresh or compacted session? (who can answer: the user, at specify)
- Should refine offer `git pull` after switching to `main`? (who can answer: the user)

## Candidate Capabilities

None: this changes skill text only, and `skills/` has no capability yet.
