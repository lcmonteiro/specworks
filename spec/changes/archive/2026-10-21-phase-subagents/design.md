# Design: phase-subagents

## Context

`/specworks-build` and `/specworks-done` read each phase skill
(`../specworks-<phase>/SKILL.md`) and follow it in the same conversation.
Claude Code subagents start from a fresh context (their prompt, CLAUDE.md, a
git status snapshot) and cannot ask the user. Copilot's subagent isolation is
not documented. See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- A phase run by build or done sees the project and the change's artifacts,
  and nothing from the chat.
- Every question a phase asks today still reaches the user, and every answer
  reaches the next run of the phase through disk.

**Non-Goals:**
- Changing what any phase does, checks or asks.
- Enforcing isolation with installed files or CLI checks.

## Decisions

### The prompt is fixed text plus the ref

Each subagent prompt is a template in the shared text with only `<ref>` and
the skills folder filled in. A go-ahead is expressed by which fixed prompt is
sent (close's "merge plan approved, continue from step 4"), never by text
taken from the chat. Alternative: pass the user's answers in the prompt;
rejected, it is the channel this change closes.

### Answers go to disk before the restart

| Question | Who writes the answer | Where |
|---|---|---|
| design: the API | coordinator | design.md `## Interfaces`, marked agreed |
| test, code: the test command | coordinator | `spec.yml` `commands:` (the project) |
| code: unclear task, test vs spec, new work | coordinator | the Decision in design.md, or a task in tasks.md |
| review: each finding | coordinator | the finding's `**Decision**:` in review.md |
| close: register a capability | coordinator | `spec.yml` via `specworks capability add` |
| close: merge and archive | none | the fixed prompt of the second close subagent |

The subagent writes its proposal into the artifact before it returns the
question (the API in design.md, `**Proposal**:` under each review finding),
so the answer is an edit to something already on disk. Alternative: the
coordinator keeps the answers and replays them; rejected, the next phase
could not see them.

### One `Result:` line ends every subagent

```
Result: done     <one-line result; gate passed>
Result: question <the closing question as the phase skill asks it>
Result: blocked  <what failed, and the phase or skill it goes back to>
```

`done` → the coordinator reports the line and starts the next phase.
`question` → ask, record (above), restart the same phase. `blocked` → the
build or done stops, as it does today when a gate cannot be fixed.
Alternative: free text; rejected, the coordinator would have to interpret it.

### Review returns all findings at once

The review subagent writes review.md with every finding open and its
`**Proposal**:`, and returns them in one `Result: question`. One subagent
round instead of one per finding, and review.md stays review's own artifact.

### No subagent tool: run it in the conversation

Where the tool has no subagent (some Copilot setups), the coordinator
follows the phase skill itself, as today. The rest of the contract (answers
to disk) still holds.

## Interfaces

None: the change edits `src/specworks/skills/specworks-build/SKILL.md` and
`src/specworks/skills/specworks-done/SKILL.md`, and adds the shared text
`src/specworks/skills/_shared/phase-subagents.md`, rendered by the existing
`<!-- specworks:include <name> -->` mechanism. Their `allowed-tools` gains
`Agent`. No API, CLI surface or data shape changes.

## Risks / Trade-offs

- [a subagent asks the user anyway or skips a question] -> the fixed prompt
  says to return every question as `Result: question`, and the coordinator
  runs each phase's gate result through the `Result:` line.
- [more subagent rounds, each re-reading the artifacts] -> accepted: that
  re-reading is the point; review batches its findings into one round.
- [the coordinator edits a phase's artifact] -> limited to recording an
  answer to a question the phase asked, in the place the table names.

## Open Questions

None.
