# Refinement: move-config-into-spec-folder

## Problem

A specworks project keeps its config at the root (`<dir>.yml`, e.g.
`spec.yml`) next to its workflow folder (`<dir>/`), and the file's name sets
the folder's name. The user asked to "change the spec.yml to config.yml and
move to [the] spec (root) folder": one folder that holds everything specworks
owns, with a fixed, hidden name like `.github/` "to be easy to find projects
and modules".

## Context

**Observed:**
- `src/specworks/core/config.py`: `find_config` takes any `*.yml` holding a
  `specworks: <n>` line in a folder; `find_root` walks up to the nearest such
  folder; `Config.dir` comes from the file name (`spec.yml` -> `spec`);
  `load_config(root, dir)` reads `root/<dir>.yml`.
- `src/specworks/core/validators.py`: `validate_dir` accepts only letters,
  digits, `-` and `_` (no leading dot).
- `src/specworks/core/workspace.py`: every module must use the workspace's
  file name (`load_module_config`, with a "rename X to Y" error);
  `_may_link` reads `*.yml` configs of parent folders.
- `specworks init --dir` picks the name (default `specworks`: `specworks.yml`
  + `specworks/`); this repo uses `spec.yml` + `spec/`.
- `src/specworks/specs/trace.py` already skips hidden folders when scanning
  tags.
- `project` living docs (`src/specworks/core/docs/`): REQ-PROJ-001 (finding
  the config; the file name sets the folder), REQ-PROJ-002 (config checks),
  REQ-PROJ-006 (workspace of modules), REQ-PROJ-009 (default config), and
  the `init` requirements.
- `spec.yml` is named in about 38 files under `src/` and `tests/`, one skill,
  the config template and the GitHub wiki.

**Assumed:**
- Anything else specworks keeps per project (the run cache, if it lives in the
  workflow folder) moves with the folder.

## Constraints

- [hard] One fixed layout: `<project>/.specworks/config.yml`, with changes in
  `.specworks/changes/active/` and `.specworks/changes/archive/`, for the top
  project and every module.
- [hard] Clean break: an old `<dir>.yml` project is not read or migrated.
- [hard] When no `.specworks/config.yml` is found but a folder holds an
  old-style config (a `*.yml` with the `specworks:` line), the CLI fails with
  an error naming the move (e.g. `found spec.yml (old layout): move it to
  .specworks/config.yml and spec/ to .specworks/`) instead of a bare
  `"root": null`. Nothing is moved automatically.
- [hard] The `specworks:` marker line stays required in `config.yml`.
- [hard] This repo moves too (`spec.yml` -> `.specworks/config.yml`,
  `spec/changes/` -> `.specworks/changes/`), in the same change.
- [soft] Living docs stay next to the code (`<path>/docs/`), so hiding the
  workflow folder hides only changes in flight.

## Options

### Option A: `<folder>/config.yml`, folder name free (default `spec/`)

The project is the folder above any `<dir>/config.yml` with the marker.

- **Pros:** keeps renaming; visible by default.
- **Cons:** a fuzzier search (two such folders in one place); not hidden.
- **Effort:** M
- **Touches:** `project`

### Option B: fixed hidden `.specworks/config.yml`

Finding a project is one check per folder while walking up:
`<folder>/.specworks/config.yml` with the marker. `--dir`, `Config.dir`
naming and the module file-name rule go away.

- **Pros:** one known path like `.github/`, easy to find for projects and
  modules; a clean root; simpler code.
- **Cons:** breaks every existing project (clean break, by choice); change
  files are hidden from file trees and some default searches; no renaming.
- **Effort:** M-L (many references, tests and docs)
- **Touches:** `project`, `cli` (`init --dir`), skills text

### Option C: keep `<dir>.yml` at the root

- **Pros:** no break.
- **Cons:** does not do what the user asked.
- **Effort:** -
- **Touches:** -

## Recommendation

Option B, chosen by the user: a fixed `.specworks/config.yml` for every
project and module, a clean break with a clear error for the old layout.

## Open Questions

- None blocking. Specify decides the exact wording of the old-layout error
  and which `project` requirements are MODIFIED or REMOVED.

## Candidate Capabilities

- `project`: modified - finding the config (REQ-PROJ-001), config checks,
  workspace of modules (REQ-PROJ-006), default config and `init`.
- `cli`: modified - `init` loses `--dir`; messages naming `<dir>.yml`.
