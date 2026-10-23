# Design: active-changes-dir

## Context

Every path to a change goes through `Config.changes_path` and `Config.archive_path` (`src/specworks/core/config.py`); `create_change`, `load_change` and `list_changes` (`src/specworks/core/changes.py`) build on them. The archive is `changes_path / "archive"` today, so `list_changes` skips an `archive` entry and `archive` is a reserved name. See proposal.md for why.

## Goals / Non-Goals

**Goals:**
- One place decides where active and archived changes live.
- Archived changes and their paths are untouched.

**Non-Goals:**
- Reading or migrating loose `<dir>/changes/<name>` folders.

## Decisions

### `changes_path` becomes the active folder, `archive_path` its sibling

`changes_dir` and `changes_path` end in `/changes/active`; `archive_path` is built from the `changes` folder, not from `changes_path`. Every caller already uses these two properties, so the CLI output (`changesDir`) and the error messages follow. Serves: REQ-PROJ-001, REQ-PROJ-010, REQ-PROJ-020. Alternative: a new `active_path` beside `changes_path`: rejected, it leaves callers free to keep using the old one.

### `list_changes` stops skipping `archive`; the reserved names stay

`archive` is no longer a sibling of the changes, so the skip goes. `create_change` still refuses `archive` and `active`, so a change name never looks like a folder name. Serves: REQ-PROJ-010, REQ-PROJ-020.

### `init` creates both folders

`<dir>/changes/active/` and `<dir>/changes/archive/` are made with the config. Serves: REQ-CLI-003.

### This change moves itself last

`spec/changes/active-changes-dir` is a loose folder once the code lands, so the code half ends with `git mv` into `spec/changes/active/` and the CLI is checked against it. Serves: REQ-PROJ-020.

## Interfaces

None. `Config.changes_dir`, `Config.changes_path` and `Config.archive_path` keep their signatures; only the folder they name changes.

## Risks / Trade-offs

- [`review` finds the start commit from the history of `.change.yaml`, which the move changes for a change in flight] -> a rename is not an add in git, and only this change is in flight; check `specworks review` after the move.
- [existing projects lose sight of their loose changes] -> stated as breaking in the proposal; they move the folders by hand.

## Migration / Rollback

None for the code. Existing projects: `mkdir spec/changes/active && git mv spec/changes/<name> spec/changes/active/` for each change in flight.

## Open Questions

None.
