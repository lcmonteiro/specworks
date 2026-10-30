# Design: add-start-skill

## Context

See proposal.md. Packaged skills are discovered from the folders under
`src/specworks/skills/` (`specworks skills` installs every one, and
`tests/test_skills.py` iterates `packaged_skills()`), so a new skill folder
needs no registration in Python code.

## Goals / Non-Goals

**Goals:**
- A new skill file on today's CLI commands (`init`, `module add`,
  `capability add`, `context`).

**Non-Goals:**
- Any CLI or library change (Options B and C of the refinement).

## Decisions

### No code API

The skill is Markdown text read by the agent; it calls only existing
commands. The only Python touched is `tests/test_skills.py`, which adds
`specworks-start` to the skills excluded from the shared change-picking
rule (next to `specworks-refine`, `specworks-adopt`, `specworks-baseline`).

## Interfaces

None: the change adds a packaged skill (Markdown text, task 1.2) and a README line; no public class, function or CLI command is added or changed.

## Diagrams

No structural change.

## Risks / Trade-offs

- [the agent judges "already has code" by reading the files] -> the skill
  names what does not count (docs, licence, git files) and hands anything
  else to `/specworks-adopt`.
