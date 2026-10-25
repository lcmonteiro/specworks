# Design: move-config-into-spec-folder

## Context

See proposal.md. Today `Config.dir` comes from the config's file name and is
used to build `<dir>/changes/...`, to skip the workflow folder when scanning
tags and changed files (`specs/trace.py`, `workflow/review.py`), and by the
run cache (`core/runner.py`). `find_config` globs `*.yml` with the marker;
`load_module_config` checks a module uses the workspace's file name;
`validate_dir` and `config_name` serve `init --dir`.

## Goals / Non-Goals

**Goals:**
- One fixed layout, `.specworks/config.yml` + `.specworks/changes/`, found by
  one path check per folder (REQ-PROJ-001, REQ-PROJ-020).
- A clear error for the old layout instead of `"root": null` (REQ-PROJ-021).
- This repo moved to the new layout in the same change.

**Non-Goals:**
- Reading or migrating old configs; a configurable folder name.

## Decisions

### `Config.dir` becomes a constant

`WORKFLOW_DIR = ".specworks"` and `CONFIG_FILE = "config.yml"` in
`core/config.py`. `Config.dir` stays as a field (always `.specworks`) so the
callers that build paths or skip the folder keep working unchanged.
Alternative: remove the field and change every caller; more churn for no
behaviour. Serves: REQ-PROJ-001, REQ-PROJ-020.

### Finding the project

`find_config(directory)` returns `directory/.specworks/config.yml` when it
exists and has the marker, else None. `find_root` walks up as today. The
"several configs in one folder" error goes away (one fixed path). Serves:
REQ-PROJ-001.

### The old layout

When `find_root` finds nothing, a second walk up looks for an old-style
config (`*.yml` with the marker, the old `find_config` rule) in the working
directory and its parents; the nearest one makes the lookup fail with a
`ConfigError` naming the file and the move. A listed module with no
`.specworks/config.yml` but an old-style config fails the same way, naming
the module. A folder with both layouts uses the new one. Serves:
REQ-PROJ-021.

### init

`--dir` is removed; `init` writes `.specworks/config.yml` from the template,
whose comments describe the fixed layout. `validate_dir` and `config_name`
are removed with their only callers. Serves: REQ-CLI-003, REQ-PROJ-009.

### Moving this repo

The code half moves `spec.yml` to `.specworks/config.yml` and `spec/` to
`.specworks/` (`git mv`) in the same commit as the code, so the CLI run from
source keeps finding the project; the active change moves with it. The test
half changes only tests, which build their sample projects through
`tests/helpers.py` and `tests/samples.py`.

## Interfaces

To be settled in the design phase. Expected:
- `src/specworks/core/config.py`: `WORKFLOW_DIR`, `CONFIG_FILE` (new);
  `find_config(directory) -> Path | None` (now `.specworks/config.yml`);
  `load_config(root) -> Config` (no `dir` argument); `config_name` removed
  (REQ-PROJ-001, REQ-PROJ-009)
- `src/specworks/core/config.py`: `find_old_config(start) -> Path | None`
  (new), the nearest old-style config (REQ-PROJ-021)
- `src/specworks/core/validators.py`: `validate_dir` removed (REQ-PROJ-009)
- `src/specworks/cli/project.py`: `init` without `--dir` (REQ-CLI-003)

## Risks / Trade-offs

- [Every existing project breaks] -> the old-layout error names the exact
  move; the README and wiki say how.
- [The repo move and the code must land together, or the source CLI cannot
  find this project mid-build] -> the code half does both in one commit; the
  test half's worktree keeps the old layout until the merge, and git's rename
  detection carries its `tasks.md` ticks over to the moved file.
- [Hidden folder: change files skipped by some search tools] -> accepted by
  the user; skills name `.specworks/changes/active/<name>/` explicitly.

## Migration / Rollback

Each project: `mkdir .specworks && git mv spec.yml .specworks/config.yml &&
git mv spec/changes .specworks/changes` (any `<dir>` in place of `spec`).
Rollback is the reverse move with the previous specworks release.

## Open Questions

None.
