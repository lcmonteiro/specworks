# Design: skill-push-step

## Context

See [proposal.md](proposal.md). Only the layout of two skill files changes; the shared text and the CLI are untouched.

## Goals / Non-Goals

**Goals:**
- The `pushing` include stands on its own in `specworks-close` and `specworks-done`.

**Non-Goals:**
- Changing what the pushing text says.

## Decisions

### The include is a block between paragraphs, like `committing`

The shared text is unindented and `INCLUDE_RE` has no indentation support, so the text after it is unindented too. Alternative: make the include indentation-aware: more code for two uses.

## Interfaces

None: only packaged skill text changes; no function, command or data shape is added or changed.

## Risks / Trade-offs

- [The skill reads slightly less nested in the source] -> the rendered list is the same, and `tests/test_skills.py` still passes.

## Open Questions

- None.
