# Review: move-config-into-spec-folder

Base: `origin/main`

## Findings

- [ ] R1 **spec-gap** `specworks init` run at the root of an old-layout project (`spec.yml` + `spec/`, no `.specworks/config.yml`) succeeds: it writes a new, empty `.specworks/config.yml` and `.specworks/changes/` beside the old files, and from then on the new layout wins (AC-PROJ-021.3), so the old-layout error never shows again and the changes in `spec/changes/active/` are silently left out (`specworks list` shows none). Run one folder lower, the same `init` fails with the old-layout error (its parent lookup goes through `find_root`). REQ-PROJ-021 says a command fails when "the working directory or one of its parents" holds an old config and no project is found, but no criterion covers `init`, which looks up only `PATH`'s parent; the two halves left it out (REQ-PROJ-021, REQ-CLI-003; `src/specworks/cli/project.py:116`)
  - **Proposal**: back to specify: add AC-PROJ-021.4 "An old project is not re-initialised": GIVEN a folder holding `spec.yml` with `specworks: 1` and no `.specworks/config.yml`, WHEN `init` runs there (with or without `--no-link`), THEN it fails with the old-layout error naming `spec.yml` and the move, and writes nothing (no `.specworks/`, no skills, no link). Then test (the criterion's test) and code (`init` without a parent project checks `old_config_in(root)` before writing and raises `old_layout_error`; a linked module and `module add` already fail through `load_module_config`)
  - **Decision**: back to specify: add AC-PROJ-021.4 as proposed, and in the same pass add REQ-CLI-005 to the delta with its wording updated for the fixed `.specworks/` folder (it still says `module add` creates "the module's config with the workspace's name"); then test and code as proposed (agreed with the user)
  - done in specify: added AC-PROJ-021.4 to REQ-PROJ-021 (init in an old-layout folder fails and writes nothing); REQ-CLI-005 MODIFIED (`module add` creates `.specworks/config.yml`; AC-CLI-005.1 and .2 reworded); tasks 3.1 [test] and 3.2 [code]; design.md notes the init check
  - done in design: no new API; design.md Interfaces: `init` with no parent project fails with `old_layout_error` (via `old_config_in(root)`) before writing, and `ensure_module_config` (`module add`) refuses an old-style folder through `load_module_config` (REQ-PROJ-021, REQ-CLI-005)

## Changed files without tags

- `tests/helpers.py`: test plumbing; the sample project is built with `init` (no `--dir`) and its config read from `.specworks/config.yml` (REQ-PROJ-001, REQ-PROJ-020)
- `tests/test_walkthrough.py`: the end-to-end walkthrough moved to the new paths (`init` without `--dir`, `.specworks/config.yml`, `.specworks/changes/...`); no criterion of its own

## Summary

The code and the delta specs agree on the fixed `.specworks/config.yml` layout, the old-layout error for a project and a module, `init` without `--dir` and the `dir` key message; 601 tests and lint pass, and the repo itself is on the new layout. One open finding: `init` at the root of an old-layout project creates a second, empty project instead of naming the move (R1, back to specify). The `specworks check` warnings for the dropped AC-PROJ-001.3, AC-PROJ-006.3, AC-PROJ-009.2 and AC-CLI-003.4 are intended (task 1.2, proposal); their tests are gone.
