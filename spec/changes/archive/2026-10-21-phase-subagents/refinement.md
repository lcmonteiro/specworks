# Refinement: phase-subagents

## Problem

`/specworks-build` and `/specworks-done` run every phase in one conversation,
so a phase can lean on what was said in the chat instead of only on the
project and the artifacts the earlier phases wrote. The user wants "the steps
[to] be a sub-agent that should depend just on the project and the artifacts
from the previous steps": each phase's result should be reproducible from
what is on disk, and the context should not keep growing phase after phase.

## Context

**Observed:**
- `src/specworks/skills/specworks-build/SKILL.md` chains design → test →
  code → review, and `specworks-done/SKILL.md` chains validate → close, by
  reading `../specworks-<phase>/SKILL.md` and following it in the same
  conversation.
- The phase skills already say to re-read specs, design, tasks and review.md
  from disk before using them, so the artifacts are meant to carry
  everything a phase needs.
- `src/specworks/schema.yaml` declares the artifact graph (`requires:`), and
  `specworks instructions <artifact> --json` returns `context` (the project)
  and `dependencies` (the earlier artifacts' paths): the input contract
  exists.
- Phases stop to ask the user in the middle of their work: design agrees the
  API, test and code confirm the test command, code pauses on unclear tasks,
  review decides each finding, and close agrees the merge plan.
- `specworks skills` installs the skills for Claude Code (`.claude/skills/`)
  and Copilot (`.github/skills/`, `.github/prompts/`); `src/specworks/tools/skills.py`
  (capability `integrations`, REQ-INTEG-005/006).
- Claude Code subagents start with a fresh context (their prompt, CLAUDE.md,
  a git status snapshot) and cannot ask the user (`AskUserQuestion` is
  removed); custom agents live in `.claude/agents/`, and a skill with
  `context: fork` runs in a subagent.

**Assumed:**
- Copilot (VS Code) can call subagents (the `agents` field of a custom
  agent), but its docs do not say their context is isolated like Claude
  Code's.
- A fresh general-purpose subagent following a phase skill does the phase as
  well as the main conversation does today.

## Constraints

- [hard] A phase subagent's prompt carries only the change ref: no summary
  of the chat, no decisions.
- [hard] A decision from the user reaches the next run of a phase only by
  being written into an artifact (`design.md`, `review.md`, ...) first.
- [hard] Every phase still follows its own skill: same steps, same gates,
  same questions to the user, now asked by the coordinator.
- [hard] Hand-run phase skills keep working as they do today.
- [soft] No CLI change: the change is skill text only (`specworks skip-specs`).
- [soft] Copilot keeps working, falling back to running the phase in the
  chat where it has no subagent tool.

## Options

### Option A: Installed agent files

`specworks skills` also writes one agent per phase
(`.claude/agents/specworks-<phase>.md`, the phase skill preloaded, a fixed
tool list without `Agent`). `/specworks-build` and `/specworks-done` call
each agent by name with only the ref.

- **Pros:** the agent file fixes the inputs and tools, so the most is
  enforced.
- **Cons:** new install, refresh and stale-file behaviour; Copilot needs its
  own `.github/agents` files or keeps today's chaining.
- **Effort:** M
- **Touches:** `integrations` (REQ-INTEG-005, REQ-INTEG-006), the build and
  done skills

### Option B: Skill text only

`/specworks-build` and `/specworks-done` start a general-purpose subagent
per phase with a fixed prompt: follow `../specworks-<phase>/SKILL.md` for
change `<ref>`, do not ask the user, return the question instead. The
coordinator asks the user, records the answer in the artifact, and starts a
fresh subagent for the phase.

```
/specworks-build (main conversation: coordinates, asks the user)
  │  prompt: "change <ref>"            ▲ returns: done | question | blocked
  ▼                                    │
subagent: one phase (design / test / code / review)
  reads: spec.yml + CLAUDE.md, ../specworks-<phase>/SKILL.md,
         the change's artifacts on disk
  writes: its own artifacts only
```

- **Pros:** the isolation asked for with no CLI change; works wherever a
  subagent tool exists.
- **Cons:** the fixed prompt is a rule the coordinator follows, not a file
  that enforces it.
- **Effort:** S
- **Touches:** the build and done skills (no capability)

Considered and left out with the user: running every phase skill in a
subagent even when run by hand; a new coordinator for the whole flow; and
recording each artifact's input hashes so `status` flags stale artifacts.

## Recommendation

Option B, agreed with the user: only `/specworks-build` and
`/specworks-done` run their phases in subagents, each started with the
change ref only, and the user's decisions go into the artifacts before a
phase is restarted. Agent files (Option A) can follow if the fixed prompt
turns out not to hold.

## Open Questions

- What exactly a phase subagent returns: done (with its one-line result),
  a question (with its numbered options), or blocked (with where and why)?
  (who can answer: user, in specify)
- How review hands back several findings to decide in one round. (who can
  answer: user, in specify)
- Whether the coordinator or the subagent commits after each phase. (who can
  answer: user)
- Whether this skill text needs a wording check in `tests/test_skills.py`,
  given the skills have no capability yet. (who can answer: user)

## Candidate Capabilities

- None: skill text only (`specworks skip-specs`); the `integrations`
  capability is unchanged under Option B.
