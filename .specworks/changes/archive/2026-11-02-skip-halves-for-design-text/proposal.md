# Proposal: skip-halves-for-design-text

## Why

A review finding whose agreed fix touches only design.md still runs a full
cycle of design, both implement halves (a worktree and two subagents) and
review, and the halves have nothing to do. The refinement chose Option A:
the review Decision says so, as `back to design only: ...`, so the cycle is
known, and agreed, before it starts.

## What Changes

- A finding's Decision can start with `back to design only:`. It routes the
  finding to design; once design records `done in design:`, the finding is
  routed to review instead of implement.
- `specworks cycle` adds the test and code halves for design only when a
  finding needs design without `only`, or needs implement, or needs that
  half. Only design-only findings → `design, review`. Design-only plus a
  code finding → `design, code, review`.
- `specworks finding decide` accepts `back to design only: ...`. Any other
  `back to <step> only:` is refused, like every other unknown form.
- `back to design:` without `only` keeps today's routing.
- Skill text:
  - `/specworks-review` proposes `back to design only:` when the agreed design
    fix needs no test or code change;
  - `/specworks-build`'s cycle rules name the shorter cycle;
  - the installed copies are refreshed.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `workflow`:
  - REQ-FLOW-010 (reading review.md: routing a design-only finding);
  - REQ-FLOW-012 (build cycles: when the halves join design);
  - REQ-FLOW-016 (writing findings: the new Decision form).

## Related requirements

- REQ-FLOW-010 modified: routes `back to design only:` to design, then to review after `done in design:`.
- REQ-FLOW-012 modified: the halves join design only when a finding needs them.
- REQ-FLOW-016 modified: `back to design only:` is an accepted Decision form.
- REQ-FLOW-011 left: the review gate reads findings through REQ-FLOW-010, and its checks are unchanged.
- REQ-CLI-011 left: `finding decide` passes the decision to REQ-FLOW-016, and its output and errors are unchanged.
- REQ-CLI-007 left: close does not read findings' steps.
- REQ-PROJ-006 left: the workspace of modules is unrelated; it matched only on "cycle".

## Impact

- `src/specworks/workflow/review.py` (routing, the Decision form),
  `src/specworks/workflow/cycle.py` (the steps), and their tests.
- `src/specworks/skills/specworks-review/SKILL.md`,
  `src/specworks/skills/specworks-build/SKILL.md`, and the installed copies.
- No new command or option. Every review.md that exists today reads as
  before.

## Out of Scope

- `only` for other steps (`back to specify only:` and the rest).
- Detecting a text-only design change from git.
- The design step deciding it afterwards (`finding done --next`).
