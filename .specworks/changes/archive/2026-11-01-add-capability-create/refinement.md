# Refinement: add-capability-create

## Problem

`specworks capability add` registers a capability in the config but never
creates its code folder. The start skill (step 5) therefore has the agent
write an empty `<module path>/<folder>/.gitkeep` by hand after each
registration so git keeps the folder: the last file that skill writes by
hand, and a step the agent can miss, or get wrong (module prefix, path).

## Outcomes

- After `specworks capability add <name> --path <folder> --create`, the code
  folder exists with an empty `.gitkeep`, and git keeps it.
- A folder that already exists is left as it is: no `.gitkeep` is added and
  no file in it changes.
- The start skill writes no file by hand any more.
- Without `--create`, `capability add` behaves as it does today.

## Context

**Observed:**
- `src/specworks/cli/project.py`: `capability_add` checks the ID prefix and
  the docs folder (REQ-PROJ-016), then calls `add_capability_entry`
  (`src/specworks/core/config_file.py`) and prints `registered <ref> -> <code
  path> (REQ-<prefix>-)` or `describe(...)` under `--json`. `--module` picks
  the owning module; the path is relative to that module's root.
- `src/specworks/skills/specworks-start/SKILL.md` step 5: "`capability add`
  does not create the folder: write an empty `.gitkeep` in each capability's
  code folder (`<module path>/<folder>/.gitkeep`) so git keeps it"; the
  Boundary and Guardrails also name the `.gitkeep` files.
- adopt, close and done also run `capability add`, always for folders that
  already exist.
- Living docs: `src/specworks/cli/docs` (REQ-CLI-005 Registering modules and
  capabilities).

**Assumed:**
- An empty `.gitkeep` is the convention the project wants (it is what the
  start skill writes today).

## Constraints

- [hard] Nothing is created when the command refuses (prefix in use, docs
  folder in use, bad path).
- [hard] An existing folder and its files are never changed.
- [hard] Errors are values: `{"error": ...}` with exit 1 under `--json`.
- [soft] Paths in the output are relative to the workspace root.

## Options

### Option A: `--create` on `capability add`

When given, after the existing checks pass, create `<module root>/<path>/`
and an empty `.gitkeep` if the folder is missing; a path that exists as a
file is refused before the config is written. The output (text and
`--json`) says whether the folder was created.

- **Pros:** one call registers and creates, so no capability is missed;
  small.
- **Cons:** a flag the other skills do not use.
- **Effort:** S
- **Touches:** cli, skills
- **Outcomes:** meets all four.

### Option B: a separate `capability scaffold` command

Creates the missing folders of every registered capability at once.

- **Pros:** also helps after hand-editing the config.
- **Cons:** a second command start must remember to run.
- **Effort:** S
- **Touches:** cli, skills
- **Outcomes:** meets all four.

### Option C: do nothing

The skill keeps writing `.gitkeep` by hand.

- **Pros:** no code.
- **Cons:** the step stays non-deterministic.
- **Effort:** none
- **Touches:** none
- **Outcomes:** meets only the last one.

## Recommendation

Option A, agreed with the user: creating the folder only when asked keeps
adopt, close and done safe (a missing folder there is usually a wrong
path), and one call per capability cannot be missed. Out of scope: creating
folders without the flag, a `scaffold` command, and changes to adopt, close
and done.

## Open Questions

- None blocking the proposal.

## Candidate Capabilities

- `cli`: modified - `capability add --create` (REQ-CLI-005).
