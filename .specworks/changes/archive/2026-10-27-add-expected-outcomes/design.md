# Design: add-expected-outcomes

## Context

The change edits text only: the refinement template
(`src/specworks/templates/refinement.md`), the refinement and proposal
instructions in `src/specworks/schema.yaml`, and the refine, specify and
baseline skills in `src/specworks/skills/` (with their installed copies).
`specworks instructions` already returns the template and instruction text
through the same keys, so no code reads the new Outcomes section. The change
is marked `skip-specs`.

## Goals / Non-Goals

**Goals:**
- Refinements record expected outcomes before the options, and specify
  covers each outcome with a requirement or lists it under Out of Scope.

**Non-Goals:**
- Any CLI, schema-key or parser change; an enforced outcome check (the
  refinement's Option B).

## Decisions

### Text only, checked by wording tests

The template, instructions and skills change; `tests/test_skills.py` checks
the new wording verbatim, as it does for other skill text. No code path is
added, so there is no API to stub. Alternative considered: a check in
`specworks check` / `trace` (Option B), left out of scope.

## Interfaces

None: the change edits template, instruction and skill text only; no class,
function, CLI command or data shape is added or changed.

## Risks / Trade-offs

- [nothing enforces outcome coverage in specify] -> the specify skill and
  proposal instruction say so explicitly; an enforced check stays an open
  question for later.
