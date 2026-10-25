# Review: move-config-into-spec-folder

Base: `origin/main`

## Findings

- [x] R1 **spec-gap** `specworks init` run at the root of an old-layout project (`spec.yml` + `spec/`, no `.specworks/config.yml`) succeeds: it writes a new, empty `.specworks/config.yml` and `.specworks/changes/` beside the old files, and from then on the new layout wins (AC-PROJ-021.3), so the old-layout error never shows again and the changes in `spec/changes/active/` are silently left out (`specworks list` shows none). Run one folder lower, the same `init` fails with the old-layout error (its parent lookup goes through `find_root`). REQ-PROJ-021 says a command fails when "the working directory or one of its parents" holds an old config and no project is found, but no criterion covers `init`, which looks up only `PATH`'s parent; the two halves left it out (REQ-PROJ-021, REQ-CLI-003; `src/specworks/cli/project.py:116`)
  - **Proposal**: back to specify: add AC-PROJ-021.4 "An old project is not re-initialised": GIVEN a folder holding `spec.yml` with `specworks: 1` and no `.specworks/config.yml`, WHEN `init` runs there (with or without `--no-link`), THEN it fails with the old-layout error naming `spec.yml` and the move, and writes nothing (no `.specworks/`, no skills, no link). Then test (the criterion's test) and code (`init` without a parent project checks `old_config_in(root)` before writing and raises `old_layout_error`; a linked module and `module add` already fail through `load_module_config`)
  - **Decision**: back to specify: add AC-PROJ-021.4 as proposed, and in the same pass add REQ-CLI-005 to the delta with its wording updated for the fixed `.specworks/` folder (it still says `module add` creates "the module's config with the workspace's name"); then test and code as proposed (agreed with the user)
  - done in specify: added AC-PROJ-021.4 to REQ-PROJ-021 (init in an old-layout folder fails and writes nothing); REQ-CLI-005 MODIFIED (`module add` creates `.specworks/config.yml`; AC-CLI-005.1 and .2 reworded); tasks 3.1 [test] and 3.2 [code]; design.md notes the init check
  - done in design: no new API; design.md Interfaces: `init` with no parent project fails with `old_layout_error` (via `old_config_in(root)`) before writing, and `ensure_module_config` (`module add`) refuses an old-style folder through `load_module_config` (REQ-PROJ-021, REQ-CLI-005)
  - done in test: `test_init_in_an_old_project_names_the_move_and_writes_nothing` (`tests/test_cli.py`, @ac AC-PROJ-021.4, with and without `--no-link`) checks exit 1, the error naming `spec.yml` and the move, no file added and the old config unchanged; the AC-CLI-005.2 test now asserts the old-layout message
  - done in code: `init` with no parent project raises `old_layout_error(old)` when `old_config_in(root)` finds an old-style config and the folder has no `.specworks/config.yml`, before writing anything (`src/specworks/cli/project.py:117`, @req REQ-PROJ-021)
  - confirmed in review (cycle 2): the AC-PROJ-021.4 test passes; the linked case (`init sub` in a project, `sub/spec.yml`) also fails with the module's old-layout error through `ensure_module_config` and writes nothing; 603 tests pass

## Changed files without tags

- `tests/helpers.py`: test plumbing; the sample project is built with `init` (no `--dir`) and its config read from `.specworks/config.yml` (REQ-PROJ-001, REQ-PROJ-020)
- `tests/test_walkthrough.py`: the end-to-end walkthrough moved to the new paths (`init` without `--dir`, `.specworks/config.yml`, `.specworks/changes/...`); no criterion of its own

## Summary

The code and the delta specs agree on the fixed `.specworks/config.yml` layout, the old-layout error for a project, a module and `init` in an old-layout folder (AC-PROJ-021.4), `module add` creating `.specworks/config.yml` (REQ-CLI-005), `init` without `--dir` and the `dir` key message; 603 tests pass. R1 (cycle 1, sent back to specify) is done: spec, test and code carried it out and it is closed; cycle 2 found nothing new. The `specworks check` warnings for the dropped AC-PROJ-001.3, AC-PROJ-006.3, AC-PROJ-009.2 and AC-CLI-003.4 are intended (task 1.2, proposal); their tests are gone.
