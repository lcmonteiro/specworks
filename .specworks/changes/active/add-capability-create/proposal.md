# Proposal: add-capability-create

## Why

`capability add` registers a capability but never creates its code folder,
so the start skill has the agent write a `.gitkeep` by hand in each new
folder. Creating it in the same call makes that step deterministic.

## What Changes

- `specworks capability add <name> --path <folder> --create`: once every
  existing check has passed, it creates the folder (relative to the owning
  module's root, as the config stores it) with an empty `.gitkeep` when the
  folder is missing. An existing folder is left as it is.
- A `--path` that exists as a file is refused before the config is written.
- The output says whether the folder was created: text
  `created <folder>/.gitkeep`, and a `created` field (the `.gitkeep` path
  relative to the workspace root, or `null`) under `--json`.
- The start skill uses `--create` instead of writing `.gitkeep` by hand.
- Without `--create`, nothing changes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `cli`: adds REQ-CLI-014 (creating a capability's code folder with
  `capability add --create`).

## Impact

- `src/specworks/cli/project.py`: the `--create` option of `capability add`.
- `src/specworks/skills/specworks-start/SKILL.md` and its installed copy.
- Tests: the new requirement, and a wording test for the start skill.

## Out of Scope

- Creating folders without `--create`.
- A `capability scaffold` command.
- adopt, close and done, which register folders that already exist.
