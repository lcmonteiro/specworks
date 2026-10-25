# Proposal: skill-push-step

## Why

The shared `pushing` text added by `git-workflow` is included in the middle of
a numbered step in `specworks-close` and `specworks-done`: the block is
unindented while the text after it is indented, and `specworks-done` has no
blank line before the include. It reads as part of the step in the source and
breaks the list in the rendered skill.

## What Changes

- In `specworks-close` and `specworks-done`, the `pushing` include stands on
  its own, with a blank line before it, and the next-steps text after it is
  unindented like the block it follows.
- The installed copies (`.claude/skills/`, `.github/skills/`,
  `.github/prompts/`) are refreshed with `specworks skills`.

## Capabilities

None: only the packaged skill text changes, and no capability holds
requirements for the skills. The change is marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- `src/specworks/skills/specworks-close/SKILL.md`,
  `src/specworks/skills/specworks-done/SKILL.md` and their installed copies.
- No CLI, API or data change. The change builds on the unmerged branch
  `git-workflow` (it edits text that branch added).

## Out of Scope

- What the pushing text says; only where and how it is placed.
- Tagging and testing skill text.
