# Proposal: clear-decision-prompts

## Why

When a skill stops for a human decision, the message does not always end with
something the user can simply answer: some stops end with an open "ask
about…" or "agree on it". The user wants every such stop, and the end of every
phase, to close with a clear yes/no question, or with numbered options with a
recommended one. The refinement chose Option A: a shared rule included in
every skill, plus each decision point reworded to follow it.

## What Changes

- New shared text `src/specworks/skills/_shared/asking-the-user.md`, included
  with `<!-- specworks:include asking-the-user -->` in every packaged skill.
  It says:
  - every stop for a human ends with exactly one closing question, which is
    either a yes/no question (`... ? (yes/no)`), or numbered options
    (`1.`, `2.`, ...) with exactly one marked "(recommended)" and a one-line
    reason;
  - nothing follows that question in the message;
  - one decision at a time, unless several are independent and asked
    together;
  - the end of a phase offers the next step as numbered options: the next
    skill (recommended), any alternative, and "stop here".
- Each open decision point is reworded to name its options and the
  recommended one:
  - adopt: the folder name, the modules, the commands, the context, the
    capability table;
  - baseline: the capability to baseline, the requirements and bug list;
  - refine: running init, continuing a change, the name and module, and
    "Ready to record?";
  - specify: questions on scope, and the requirements table;
  - design: the API list;
  - test and code: the test command, and code's "Pause and ask";
  - review: each finding's proposal;
  - build: "Start cycle N?";
  - close: registering a capability, and "Merge and archive?".
- Each phase end ("When you are ready, run ...") becomes a choice of next
  steps:
  - refine → specify;
  - specify → build (recommended) or design;
  - design → test;
  - test → code;
  - code → review;
  - review → done, or validate;
  - build → done, or validate;
  - validate → close, or the phase to go back to;
  - close and done → the next baseline or a PR;
  - adopt → the first baseline;
  - baseline → done.
- The installed copies (`.claude/skills/`, `.github/skills/`,
  `.github/prompts/`) are refreshed with `specworks skills`.

## Capabilities

None: only the packaged skill text changes, and no capability holds
requirements for the skills (the skills capability is deferred). The change is
marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- Every `src/specworks/skills/*/SKILL.md`, the new
  `_shared/asking-the-user.md`, and the installed copies.
- No CLI, API or data change. `tests/test_skills.py` renders every skill, so a
  missing include fails there.

## Out of Scope

- Tool-specific question widgets (e.g. Claude Code's AskUserQuestion). The
  rule is about the text, and a tool may present it as a widget.
- Changing what the skills decide or when they stop; only how the stop is
  worded.
- Tagging and testing skill text (the deferred skills capability).
