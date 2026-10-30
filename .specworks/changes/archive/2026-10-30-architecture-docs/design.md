# Design: architecture-docs

## Context

See [proposal.md](proposal.md). Only the design instruction in
`src/specworks/schema.yaml`, the design template, four packaged skills and
three comments change; `specworks instructions` returns the new text through
the same keys, and no CLI behaviour changes (`skip-specs`).

## Goals / Non-Goals

**Goals:**
- A structural change's `design.md` has a block diagram, or says "No
  structural change" under `## Diagrams`.
- Close keeps one block diagram of the capability in its living `design.md`;
  baseline draws the first one; nothing mentions `architecture.md`.

**Non-Goals:**
- Checking the rule in `gate design` or validate (the refinement's Option B).

## Decisions

### The rule lives in the design instruction; the skills point to it

The instruction (and the template comment that mirrors it) states the rule
once; specify step 6, close step 4 and baseline step 5 follow it rather than
restating the D2 rules. Alternative: repeat the rule in each skill: more text
to keep in step.

## Interfaces

None: only instruction, template, skill and comment text changes; no
function, command or data shape is added or changed.

## Diagrams

No structural change.

## Risks / Trade-offs

- [Nothing checks that design followed the rule] -> the "No structural
  change" line makes the decision visible in review; a gate warning can
  follow as its own change.

## Open Questions

- None.
