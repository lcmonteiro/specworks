# Design: ignore-vscode

## Context

See [proposal.md](proposal.md). One line is added to `.gitignore`.

## Goals / Non-Goals

**Goals:**
- `git status` no longer lists `.vscode/`.

**Non-Goals:**
- Changing any other ignore rule.

## Decisions

### The rule goes before the trailing D2 comment

The last line of `.gitignore` is a comment about the D2 binary; a rule after it
would read as belonging to that comment.

## Interfaces

None: no function, command or data shape is added or changed.

## Risks / Trade-offs

- [None worth recording] -> a one-line ignore rule.

## Open Questions

- None.
