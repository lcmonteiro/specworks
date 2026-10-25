# Proposal: move-config-into-spec-folder

## Why

The project config sits at the root as `<dir>.yml`, and its file name sets
the workflow folder's name. The user wants one fixed, hidden folder that holds
everything specworks owns, like `.github/`, so projects and modules are easy to
find. The refinement chose Option B: always `.specworks/config.yml`, as a clean
break.

## What Changes

- **BREAKING** The project config is `.specworks/config.yml` (with the
  `specworks: <n>` line), and changes live in `.specworks/changes/active/`
  and `.specworks/changes/archive/`, for the top level and every module. A
  project is a folder holding `.specworks/config.yml`; it is found by walking
  up from the working directory.
- **BREAKING** A `<dir>.yml` at a project's root is no longer read. When no
  project is found but the working directory or a parent holds an old-style
  config (a `*.yml` with the `specworks:` line), the CLI fails with an error
  naming the move (`move spec.yml to .specworks/config.yml and spec/ to
  .specworks/`). A module listed by its parent that still has the old layout
  fails the same way, and so does `init` in a folder that still has the old
  layout. Nothing is moved automatically.
- **BREAKING** `specworks init` loses `--dir`; it always writes
  `.specworks/config.yml`. The rule that a module uses the workspace's config
  file name, and its "rename" error, go away, and so do the checks on a
  folder name.
- The old `dir:` key error now says the workflow folder is always
  `.specworks/`.
- This repo moves to the new layout: `spec.yml` -> `.specworks/config.yml`,
  `spec/changes/` -> `.specworks/changes/`. Skills, templates, the config
  template and help texts name `.specworks/config.yml`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `project`: REQ-PROJ-001 (finding the config), REQ-PROJ-002 (the old `dir`
  key message), REQ-PROJ-006 (modules: no shared file name), REQ-PROJ-009
  (default config), REQ-PROJ-010 and REQ-PROJ-020 (where changes live), and
  a new REQ-PROJ-021 (the old layout).
- `cli`: REQ-CLI-003 (init without `--dir`), REQ-CLI-005 (`module add`
  creates the module's `.specworks/config.yml`; an old-style config is refused
  with the old-layout error).

## Impact

- `src/specworks/core` (config, config file template, workspace,
  validators, changes), `src/specworks/cli` (init and messages naming the
  config), the skills and templates that name `spec.yml`, and the tests that
  build sample projects (`tests/helpers.py`, `tests/samples.py`).
- Every existing specworks project must move its config and folder by hand.
- The GitHub wiki needs the new layout (outside this repo).

## Out of Scope

- An automatic migration (`specworks migrate`) or reading old configs.
- A configurable folder name or a visible (non-hidden) default.
- Moving living docs: they stay next to the code in `<path>/<docs_dir>/`.
