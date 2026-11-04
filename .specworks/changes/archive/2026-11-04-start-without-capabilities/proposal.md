# Proposal: start-without-capabilities

## Why

`/specworks-start` makes the user name capabilities (name, code folder, ID
prefix) on an empty repository, before any behaviour is known; those guesses
become config. Capabilities are better proposed per change, in refinement,
once the behaviour is being discussed (see refinement.md, Option A).

## What Changes

- `specworks-start`: the proposed tree has no capabilities. It is the minimal
  tree `.specworks/`, `docs/` (with `architecture.md`), `src/` and `tests/`,
  plus the context and commands; in a multi-module tree, each module gets the
  same four. The create step no longer runs `capability add`; it writes
  `src/.gitkeep` and `tests/.gitkeep` (per module) itself, and the first
  architecture says no capability exists yet (no block diagram until one
  does). Boundary, guardrails and hand-over follow.
- `specworks-onboard`: a project with no capabilities is routed by its
  state: changes in flight go by their phase; a fresh config (empty context
  and commands) goes to `/specworks-start` (no code) or `/specworks-adopt`
  (code); a started project (context or commands set, no code) goes to
  `/specworks-refine`.
- Refinement: `## Candidate Capabilities` asks, for a new capability, its
  owning module, code path and one-line description (template, schema
  instruction and the refine skill's guardrail).
- README: `/specworks-start` described without capabilities.
- `tests/test_skills.py`: the start tests that require `capability add` and
  forbid a hand-written `.gitkeep` are replaced by tests for the new wording.
- Installed skill copies refreshed with `uv run specworks skills`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- None: skill text, templates and README only; `skills/` has no capability
  yet. Marked `specworks skip-specs`.

## Related requirements

- REQ-CLI-014 left: `capability add --create` stays; start just stops using it.
- REQ-CLI-005 left: registering capabilities is unchanged; close still does it.
- REQ-PROJ-016 left: unique docs folders are unchanged.

## Impact

- `src/specworks/skills/specworks-start/SKILL.md`,
  `src/specworks/skills/specworks-onboard/SKILL.md`,
  `src/specworks/skills/specworks-refine/SKILL.md`
- `src/specworks/templates/refinement.md`, `src/specworks/schema.yaml`
  (refinement instruction)
- `README.md`, `tests/test_skills.py`, installed copies under `.claude/skills/`
- No CLI, config or data change.

## Out of Scope

- A CLI command that creates the tree (refinement Option B).
- Removing `capability add --create` (REQ-CLI-014).
- Changing `/specworks-adopt`, which still maps existing code to capabilities.
- Giving the skills a capability of their own.

Assumptions: each module of a multi-module tree gets its own `src/`, `tests/`,
`docs/architecture.md` and `.specworks/`; the first architecture has no block
diagram until the first capability is registered.
