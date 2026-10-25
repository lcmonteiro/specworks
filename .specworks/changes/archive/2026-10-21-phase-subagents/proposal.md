# Proposal: phase-subagents

## Why

`/specworks-build` and `/specworks-done` run every phase in one conversation,
so a phase can lean on the chat instead of only on the project and the
artifacts the earlier phases wrote. The user wants each step to be a subagent
that depends only on those. The refinement chose Option B: skill text only,
with the decisions the user makes carried back through the artifacts.

## What Changes

- `/specworks-build` runs design, test, code and review, and `/specworks-done`
  runs validate and close, each in a fresh subagent. The prompt is fixed text
  from the skill plus the change ref: never a summary of the chat, never a
  decision.
- A new shared text `src/specworks/skills/_shared/phase-subagents.md`,
  included in both skills, holds the contract:
  - the fixed prompt: follow `<skills dir>/specworks-<phase>/SKILL.md` for
    `<ref>`, read only the project and the change's artifacts, do not ask the
    user;
  - before stopping for a decision, the subagent writes what it proposes into
    its own artifact, then returns the question;
  - its final message ends with one `Result:` line: `done` (one-line result,
    gate passed), `question` (the closing question as the phase skill asks
    it, options included) or `blocked` (what failed and where it goes back
    to);
  - the coordinator asks the user, writes the answer to disk (the artifact
    the question is about, or the project through the CLI), and starts a
    fresh subagent for the same phase.
- Review in a build writes every finding open with `**Proposal**:` and
  returns them in one `Result: question`. The coordinator asks them one at a
  time (small, obvious ones grouped, as review does today), turns each answer
  into the finding's `**Decision**:` line, and a fresh review subagent
  finishes `review.md` and its gate.
- Close in a done run: the coordinator writes capability registrations to
  `spec.yml` with `specworks capability add`. The first close subagent stops
  after the dry run with the merge plan as its question. On yes, a second one
  starts with the fixed "merge plan approved, continue from step 4" prompt;
  on no, nothing is written.
- Where no subagent tool exists (some Copilot setups), the coordinator runs
  the phase in the conversation as today.
- `allowed-tools` of both skills gains `Agent`.
- Untagged wording checks in `tests/test_skills.py`, and the installed
  copies refreshed with `specworks skills`.

## Capabilities

None: only packaged skill text changes, and no capability holds
requirements for the skills. The change is marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- `src/specworks/skills/specworks-build/SKILL.md`,
  `src/specworks/skills/specworks-done/SKILL.md`, the new
  `_shared/phase-subagents.md`, `tests/test_skills.py`, and the installed
  copies (`.claude/skills/`, `.github/skills/`, `.github/prompts/`).
- No CLI, API or data change.

## Out of Scope

- Hand-run phase skills: they keep talking to the user directly.
- Installed agent files (`.claude/agents/`, `.github/agents/`).
- Recording input hashes so `status` flags stale artifacts.
- A coordinator for the whole flow (refine to close).
- Committing after each phase: no skill commits today.
