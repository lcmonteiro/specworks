# Proposal: share-skill-rules

## Why

"Back from review", the gate-fail stop and the missing test command are
written by hand in each skill that needs them, differing only in a phase
name or a sentence, and the copies drift. Shared includes cannot hold them
because an include is copied verbatim.

## What Changes

- Includes take parameters:
  `<!-- specworks:include <name> key=value key2="two words" -->`. Each
  `{{key}}` in the shared file is replaced by its value when the skill is
  filled in.
- A `{{key}}` left unfilled, or a key the shared file does not use, makes
  filling in the skill fail, naming the skill, the include and the key;
  `specworks skills` then writes nothing.
- Includes without parameters are filled in as today.
- New shared files `back-from-review.md`, `gate-fails.md` and
  `test-command.md`; `specworks-design`, `specworks-test` and
  `specworks-code` use them with parameters, keeping their current wording.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `integrations`: adds REQ-INTEG-007 (includes with parameters).

## Impact

- `src/specworks/tools/skills.py`: the include pattern and filling in.
- `src/specworks/skills/_shared/` (three new files), the three skills, and
  their installed copies.
- Tests for the requirement; the existing wording tests stay green.

## Out of Scope

- "Starting the phase" (the gates differ per phase) and "re-read from
  disk".
- Specify's back-from-review steps, and the wording in adopt and start.
