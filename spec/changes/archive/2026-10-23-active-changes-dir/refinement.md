# Refinement: active-changes-dir

## Problem

Changes in flight are folders directly under `spec/changes/`, next to `archive/`. The folder mixes active work with the archive, so it is not obvious at a glance which entries are in flight. The user asked for "something like `spec/changes/active`" for the in-progress changes.

## Context

**Observed:**
- `core/config.py`: `changes_dir` is `<dir>/changes`, `changes_path` is its path and `archive_path` is `changes_path/archive`. Every create, load and list goes through `changes_path` (`core/changes.py`).
- `core/changes.py`: `list_changes` skips the `archive` entry; `archive` is a reserved change name (`create_change`, `load_change`).
- `cli/project.py`: `init` creates `archive_path` and prints `ready   spec/changes/`; `cli/output.py` and `cli/project.py` report `changesDir` in `context` and `status --json`.
- Living docs that state the layout: `project` spec (REQ-PROJ-010 `<dir>/changes/<name>`) and `cli` spec (`init` creates `<dir>/changes/archive/`).
- Hardcoded `spec/changes/<name>` paths: the skills (`specworks-close`, `specworks-done`), the CI smoke test, `spec.yml`'s comment and about 20 test files.
- `workflow/review.py` `change_start` finds the change's start commit from the git history of its `.change.yaml`; moving a change could shift it (affects only a change in flight during the move).
- This repo has no change in flight apart from this one.

**Assumed:**
- Nothing else reads `changes/` by scanning the folder; the code goes through `changes_path` and `archive_path`.

## Constraints

- [hard] `active` is a reserved change name, like `archive`, so a change cannot shadow the folder.
- [hard] No migration: loose `spec/changes/<name>` folders of existing projects are not read, and the user moves them by hand.
- [hard] Archived changes keep working where they are (`spec/changes/archive/<date>-<name>`).
- [soft] `changesDir` in `context` and `status --json` reports where changes are created.

## Options

### Option A: `spec/changes/active/<name>` and `spec/changes/archive/`

`changes_path` becomes `<dir>/changes/active`; `archive_path` stays `<dir>/changes/archive`, now a sibling instead of a child. `init` creates both; `active` is a reserved name.

- **Pros:** one new level, `changes/` holds both states, archive paths unchanged.
- **Cons:** one more directory level in every change path; existing projects need a manual move.
- **Effort:** S
- **Touches:** `project`, `cli`

### Option B: `spec/active/<name>` and `spec/archive/`

Drops `changes/` and moves the archive too.

- **Pros:** shorter paths.
- **Cons:** breaks every archived path and reference, including `requirements.md` History links.
- **Effort:** M
- **Touches:** `project`, `cli`, `specs`

### Option C: keep `spec/changes/<name>`

- **Pros:** nothing to change.
- **Cons:** the stated problem stays.
- **Effort:** S
- **Touches:** none

## Recommendation

Option A, agreed with the user. No migration, no support for the old layout.

## Open Questions

- None blocking.

## Candidate Capabilities

- `project`: modified - changes live under `<dir>/changes/active/`, `active` is a reserved name.
- `cli`: modified - `init` creates `active/` and `archive/`, and reports `changesDir` as the active folder.
