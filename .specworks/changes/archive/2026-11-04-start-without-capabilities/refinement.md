# Refinement: start-without-capabilities

## Problem

On a greenfield project, `/specworks-start` asks the user to name capabilities
(name, code folder, ID prefix) before any code or behaviour exists. Those
guesses become config and folders that later changes must live with. The
capabilities are only known once real changes are refined.

## Outcomes

- On an empty repository, `/specworks-start` proposes and creates a tree with
  no capabilities: `.specworks/`, `docs/` (with `architecture.md`), `src/` and
  `tests/` (each kept with a `.gitkeep`), plus the context and commands.
- Capabilities are first proposed in a change's `refinement.md` under
  `## Candidate Capabilities`, each one new or modified, with its module, code
  path and one-line description. New ones are registered at close, as today.
- After start, `/specworks-onboard` sends a project with no capabilities but a
  filled context or commands to `/specworks-refine`, not back to
  `/specworks-start`.

## Context

**Observed:**
- `src/specworks/skills/specworks-start/SKILL.md`: step 4 proposes the
  capabilities in the tree, and step 5 registers them with
  `capability add --create` (one `.gitkeep` per code folder). Its boundary and
  guardrails name capabilities and `capability add --create`.
- `src/specworks/templates/refinement.md` already has
  `## Candidate Capabilities` (`new | modified - why`), and its rule in
  `src/specworks/schema.yaml` asks for the owning module of a new capability,
  but not its code path or description.
- An unregistered capability already works from specify to close:
  `specworks check` warns "not registered; register it before closing"
  (`specs/check.py`), and the close and done skills register it (step 2,
  `capability add`). Test scoping falls back to the full suite for a test
  folder that does not exist (`workflow/checks.py`).
- `src/specworks/skills/specworks-onboard/SKILL.md` maps "`capabilities` is
  empty" to `/specworks-start` when there is no code.
- `tests/test_skills.py` checks start's wording, e.g. that the create step
  runs `specworks capability add` and writes a `.gitkeep`.
- `README.md` describes `/specworks-start`.
- `capability add --create` is REQ-CLI-014 (`cli`).

**Assumed:**
- In a multi-module tree, each module gets its own `src/`, `tests/`,
  `docs/architecture.md` and `.specworks/`.
- `capability add --create` stays in the CLI, though start no longer uses it.

## Constraints

- [hard] Start writes no language files (no manifest, sources or tests); the
  first change sets up the stack.
- [hard] Nothing is written before the user approves the tree.
- [hard] Skills are edited in `src/specworks/skills/` only, then refreshed
  with `uv run specworks skills`.
- [soft] No CLI change; the change is skill text and templates (`skip-specs`).

## Options

### Option A: Skill text only

Start proposes the minimal tree with no capabilities and writes `src/.gitkeep`
and `tests/.gitkeep` itself, alongside `docs/architecture.md`. The refinement
rule for Candidate Capabilities also asks for the code path and a one-line
description. Onboard sends a started project with no capabilities to refine.

- **Pros:** smallest change; reuses the existing path where close registers
  new capabilities.
- **Cons:** the folders are written by the skill, not checked by the CLI.
- **Effort:** S
- **Touches:** skills (start, onboard, refine), refinement template/schema,
  README; no capability
- **Outcomes:** meets all three.

### Option B: CLI creates the tree

A new command (or `init --scaffold`) creates `src/`, `tests/` and `docs/`
with `.gitkeep`, and the skills call it.

- **Pros:** the layout is created and tested by the CLI.
- **Cons:** new CLI surface and requirements for two empty files; fixes the
  layout in code.
- **Effort:** M
- **Touches:** `cli`, `project`, skills
- **Outcomes:** meets all three.

### Option C: Capabilities optional in start

Start asks whether to define capabilities now or defer them to the first
change (defer recommended).

- **Pros:** keeps today's path for users who know their capabilities.
- **Cons:** still asks the question; two ways to start.
- **Effort:** S
- **Touches:** skills (start, onboard)
- **Outcomes:** meets the first only when deferred; meets the other two.

## Recommendation

Option A, agreed with the user: no capabilities at start, the minimal tree
`.specworks/`, `docs/`, `src/`, `tests/`, and capabilities proposed in each
change's refinement and registered at close.

## Open Questions

- None blocking.

## Candidate Capabilities

- None: skill text, template and README only (`skills/` has no capability
  yet), so the change is `specworks skip-specs`.
