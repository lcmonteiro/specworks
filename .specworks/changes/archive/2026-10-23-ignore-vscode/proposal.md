# Proposal: ignore-vscode

## Why

`.vscode/` is editor state and shows up as untracked in every checkout. It is
never committed, so each phase has to remember to leave it out.

## What Changes

- `.vscode/` is added to `.gitignore`.

## Capabilities

None: only repository tooling changes. The change is marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- `.gitignore` only. No CLI, API or data change.

## Out of Scope

- Any other ignore rule.
