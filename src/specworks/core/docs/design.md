# Design: project

## Overview

The project model, in `src/specworks/core`, is what every other capability
builds on:
- **Config** (`config.py`, `validators.py`): finding the project's `<dir>.yml`
  and loading it into a validated `Config` (capabilities, modules, globs,
  commands, diagram settings).
- **Config file** (`config_file.py`): writing the default config, and adding
  module and capability entries.
- **Workspace** (`workspace.py`): the top-level project and its modules, and
  what each module inherits.
- **Changes** (`changes.py`): changes in flight and archived, and their phases
  (`refine, specify, design, implement, review, validate, close, done`).
- **Runner** (`runner.py`): running the project's own commands and reusing
  their results.
- **Helpers** (`files.py`, `git.py`, `errors.py`): reading project files,
  running git, and the user-facing error types.

## Decisions

### The config file names the workflow folder

`spec.yml` means the `spec/` folder. A `specworks: <n>` line marks the file, so
an unrelated `docs.yml` is never taken for a config. Modules must use the top
level's file name, so one name holds across the whole workspace.
(baseline-project)

### Modules are linked explicitly, like git submodules

A parent lists each module under `modules:`. Looking up the workspace rises
from the nearest config only through ancestors that list it. A broken outer
config that doesn't list the project is ignored, so an unrelated project
around it can't break it. Context is inherited top level first, and commands
are overridden key by key. A folder is at most one module: loading records each
module's resolved folder before loading its children, so a symlink back to an
ancestor, or a folder linked twice, fails with an error naming both instead of
recursing or loading the folder under two names.
A module must be listed by the innermost module holding its folder: one listed
further up fails with an error naming the module it belongs under, so the
workspace has the same shape from every folder. A module's folder, with
symlinks resolved, must be inside the top level's, so every path the CLI prints
is relative to the root; it is checked before the module's config is read.
Supporting modules outside the workspace was rejected: every path is resolved,
so each one would need rethinking.
(baseline-project, module-cycle-detection, module-add-nested, module-outside-workspace)

### Each capability owns its ID prefix and its docs folder

A workspace refuses to load when two capabilities, in any modules, share an ID
prefix, given or derived, or resolve to the same living-docs folder
(`<module root>/<path>/<docs_dir>`). Either would let one capability's
requirements land in the other's IDs or spec.md. Nested paths are fine.
`capability add` checks both before writing, against the path as the config
will store it, so its error names the capability that owns the prefix or
folder. Sharing a folder on purpose (one docs file per capability) was rejected
as unasked-for. (baseline-project, unique-capability-paths)

### Config edits keep comments

Entries are added by editing the config as text, never by dumping YAML. The
file is then re-read, and the edit is undone, with an "add it by hand" message,
when the result isn't the expected mapping. (baseline-project)

### Command results are reused on an identical tree

The fingerprint covers the command, the folder, `HEAD`, the diff, and the
untracked files with their contents, leaving out the workflow folders. Every
real run replaces the stored result, so `specworks run` can refresh a result
the fingerprint can't see changing. The store sits inside `.git/` and keeps
the 50 newest runs. Reuse is off without git, with `SPECWORKS_RUN_CACHE=0`,
when a submodule holds untracked files, and when an untracked file can't be
read: whenever the fingerprint can't see the whole tree, the command runs for
real rather than risk a stale result. Untracked names count as the raw bytes
git reports, so a name that isn't UTF-8 is fingerprinted like any other.
(baseline-project, run-reuse-unreadable-files)

### `test` and `code` are the halves of `implement`, not phases

`PHASES` has one `implement` phase; `HALVES = ("test", "code")` names its two
halves, which keep their own gates, task markers, review routing and cycle
steps. A `.change.yaml` saved in `test` or `code` is read as `implement` (no
rewrite on read; the next `set_phase` saves `implement`), so no migration step
is needed. `set_phase` refuses a half with an error naming `implement`.
Aliases that move the change to implement were rejected: two names for one
phase. (parallel-test-code)

### A project needs git, and a change gets its own branch

`require_repo(path)` fails unless the folder is inside a git repository, running
git from the nearest existing parent because `init` may be given a folder that
does not exist yet. `GitMissing(GitError)` marks "git cannot be run", so
every existing `except GitError` keeps working. A change's branch is its ref
with `:` replaced by `/` (`billing/tax/add-login` for a nested module). Creating
it is planned first and done second: `plan_branch` has no side effects and
refuses an existing branch or a detached HEAD; `create_branch` is the only
writer, using `git checkout -b` (no minimum git version, carries uncommitted
changes, works before the first commit). The base branch is passed in rather
than found in core, because `detect_base` lives in the workflow layer; a base of
`origin/main` counts as `main`. Rolling back a created branch on error was
rejected: more states to undo. (git-workflow)

### Active and archived changes live in sibling folders

`Config.changes_dir` and `changes_path` name `<dir>/changes/active`, and
`archive_dir` and `archive_path` name its sibling `<dir>/changes/archive`, both
built from the `changes` folder. Every caller goes through these properties, so
the CLI's `changesDir` and the error messages follow. `list_changes` no longer
skips `archive`, and a folder with a `.change.yaml` directly under
`<dir>/changes/` is not a change; there is no migration. `create_change` still
refuses `archive` and `active`, so a change name never looks like a folder
name. A new `active_path` beside `changes_path` was rejected: callers could keep
using the old one. (active-changes-dir)

### Expected failures are `SpecworksError`s

Bad configs, unknown changes, unreadable files and git failures all raise a
`SpecworksError` subclass with a message for the user. The CLI prints it and
exits 1. A message never suggests a fix the config would refuse: `run_command`
refuses a key that is not a command key, listing the valid ones, before saying
where to configure one. (baseline-project, run-unknown-key)

## Interfaces

- `src/specworks/core/config.py`: `find_root(start) -> Path | None`,
  `load_config(root, dir=None) -> Config`, `Config` (`changes_dir`,
  `changes_path`, `archive_dir`, `archive_path`), `Capability`,
  `DiagramSettings`.
- `src/specworks/core/workspace.py`: `load_workspace(start=None) -> Workspace | None`,
  `require_workspace(start) -> Workspace`, `Workspace` (`modules`,
  `module(name)`, `split(ref)`, `context_chain`, `merged_context`, `commands`,
  `owner(path)`, `capabilities`, `prefixes`, `docs_folder(module, path)`, `docs_folders`), `Module`,
  `capability_prefix(module_name, name, prefix="")`.
- `src/specworks/core/config_file.py`: `write_default_config`,
  `add_module_entry`, `add_capability_entry`.
- `src/specworks/core/changes.py`: `PHASES`, `HALVES`, `Change`, `create_change`,
  `load_change`, `list_changes`, `list_archived`, `archived_as`, `set_phase`.
- `src/specworks/core/runner.py`: `run_command`, `cached_run`, `RunResult`.
- `src/specworks/core/files.py`: `read_text(path, keep_newlines=False)`.
- `src/specworks/core/git.py`: `git`, `git_text`, `GitError`, `GitMissing`,
  `require_repo(path)`, `branch_name(ref)`, `Branch` (`name`, `started_from`),
  `plan_branch(cwd, name, base=None)`, `create_branch(cwd, branch)`.

## Constraints

- No dependency on the CLI, specs or workflow layers: they build on this one.
- Every path the CLI prints is relative to the workspace root
  (`Workspace.rel`).
