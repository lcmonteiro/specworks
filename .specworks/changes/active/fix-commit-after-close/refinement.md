# Refinement: fix-commit-after-close

## Problem

The close and done skills commit with `specworks commit --change "<ref>"`
after `specworks close`, but close has already moved the change to
`changes/archive/<date>-<name>/`, and `specworks commit` only finds active
changes: it refuses with `change '<ref>' is archived at …, not active`. So
every `/specworks-close` and `/specworks-done` run fails at its commit, as
the close of `commit-command` did (committed by hand). Separately, the
`alreadyDirty` list names the change's own files (its `.change.yaml` is
written at every phase move), which hides the cases that matter. (Source:
the close of `commit-command`, paraphrased.)

## Outcomes

- After `specworks close`, `specworks commit --change <ref>` commits the
  archived change: its archive folder and the removal of its active folder;
  with no `--message`, the subject is `<ref>: close`.
- `alreadyDirty` never lists a file of the change's own folder.
- A ref that is neither an active nor an archived change is still an error.

## Context

**Observed:**
- `src/specworks/cli/changes.py`: `commit` finds the change with
  `require_change`, active changes only.
- `src/specworks/core/changes.py`: `archived_as(cfg, name)` returns the
  newest archived change with that name; `commit_phase` stages the change
  folder plus every dirty file not in the record or with another hash, and
  `already_dirty` is every committed path that is in the record.
- After close, the archived `.change.yaml` has phase `done` and the record
  taken when close started; the active folder's files are dirty (deleted)
  and not in that record unless they were dirty already.

**Assumed:**
- The newest archived change with the name is the one close just archived.

## Constraints

- [hard] An active change with the name always wins over an archived one.
- [hard] Nothing else of REQ-PROJ-024 changes: the same files, never push,
  the detached-HEAD refusal.

## Options

### Option A: `commit` falls back to the archived change

With no active change of that name, `commit` uses the newest archived one;
its default subject is `<ref>: close`; `already_dirty` leaves out the
change's own folder.

- **Pros:** the close and done skills work as written; small.
- **Cons:** `commit` can now commit an old archived change by name, which
  only matters if someone asks for it.
- **Effort:** S
- **Touches:** `project`, `cli`
- **Outcomes:** meets all three.

### Option B: close commits before archiving

The close skill commits before `specworks close`.

- **Pros:** no CLI change.
- **Cons:** the archive move itself is then left uncommitted and needs a
  second, hand-made commit.
- **Effort:** S
- **Touches:** none (skill text)
- **Outcomes:** fails the first.

## Recommendation

Option A, agreed with the user: the skills work as written and the change is
small.

## Open Questions

- None.

## Candidate Capabilities

- `project`: modified - REQ-PROJ-024 (committing an archived change; the
  already-dirty list)
- `cli`: modified - REQ-CLI-012 (`commit` finds an archived change)
