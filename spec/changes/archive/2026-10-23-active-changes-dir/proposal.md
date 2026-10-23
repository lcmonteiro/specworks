# Proposal: active-changes-dir

## Why

Changes in flight are folders directly under `<dir>/changes/`, next to `archive/`, so the folder mixes active work with the archive. Giving the active ones their own folder makes the two states plain (see refinement.md, option A).

## What Changes

- Changes are created, found and listed in `<dir>/changes/active/<name>`; `<dir>/changes/archive/` stays as it is.
- `init` creates `<dir>/changes/active/` and `<dir>/changes/archive/`.
- `active` becomes a reserved change name, like `archive`.
- **BREAKING**: a folder with a `.change.yaml` directly under `<dir>/changes/` is no longer a change. There is no migration; existing projects move their folders into `active/` by hand.
- Skills text, the CI smoke test and the tests that spell `spec/changes/<name>` are updated to the new path.

## Capabilities

### Modified Capabilities

- `project`: REQ-PROJ-001 (a change goes to `<dir>/changes/active/<name>`), REQ-PROJ-010 (created under `active/`; `active` reserved), and a new REQ-PROJ-020 (where active and archived changes live; loose folders are not changes).
- `cli`: REQ-CLI-003 (`init` creates `<dir>/changes/active/` and `<dir>/changes/archive/`).

## Impact

- Code: `Config.changes_path` and `archive_path` in `src/specworks/core/config.py`; `create_change`, `load_change` and `list_changes` in `src/specworks/core/changes.py`; `init` in `src/specworks/cli/project.py`.
- Output: `changesDir` in `context` and `status --json`, and the `ready` line of `init`, show the active folder.
- Text: the `specworks-close` and `specworks-done` skills (and their installed copies), `spec.yml`'s comment, `.github/workflows/ci.yml`, and about 20 test files.
- A change in flight during the move may get a different start commit in `review` (it is found from the history of its `.change.yaml`).

## Out of Scope

- Migrating or reading loose `<dir>/changes/<name>` folders.
- Moving the archive, or renaming `changes/`.
- Changing the archive's `<date>-<name>` folders or the `requirements.md` History.
