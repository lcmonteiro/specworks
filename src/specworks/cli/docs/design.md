# Design: cli

## Overview

The `specworks` command line (Typer) in `src/specworks/cli`. It is a thin layer:
each command resolves the workspace and the change, calls the capability that
does the work (`project`, `specs`, `workflow`, `integrations`), and prints the
result as text or JSON.
- `app.py`: the Typer app and its command groups (`module`, `spec`, `task`,
  `capability`).
- `output.py`: the shared options, output, errors, and resolving the workspace
  and changes.
- `project.py`: `init`, `skills`, `context`, `list`, `module`, `capability`.
- `changes.py`: `new`, `status`, `abandon`, `phase`, `skip-specs`,
  `instructions`, `task`.
- `specs.py`: `check`, `trace`, `spec`, `diagrams`.
- `workflow.py`: `gate`, `start`, `review`, `cycle`, `validate`, `close`,
  `run`.
- `__init__.py`: `main` and the order commands are registered in.

## Decisions

### Agents read JSON, errors are values

Every command an agent reads takes `--json`. Commands just raise a
`SpecworksError`. The app's `command` decorator turns it into `{"error": …}`
(or `error: …` on stderr) and exit 1, and `main` does the same for errors raised
before a command runs. With no project, the answer is `{"root": null, "fix": …}`,
so a skill can tell "not set up" from a crash. (baseline-cli)

### Paths are relative to the workspace root

Every path printed is relative to the top-level project, which `context` prints
as `root`. An option that names a folder of the workspace (`diagrams --dir`) is
read from the root too, so a printed path works from any folder, and a folder
that doesn't exist is refused. `init <path>` and `module add <path>` stay
relative to the working directory: they name a folder where the user stands.
(baseline-cli, diagrams-dir-root)

### A change reference is forgiving but never ambiguous

`module:name` is exact. A bare name prefers the current module, then the only
module that has it. Archived changes are readable only through `status`, and
every other command says where the change was archived. (baseline-cli)

### The CLI checks what its own options combine into

The commands refuse option combinations that would skip a safeguard: `close`
runs validate first and takes `--no-run` only with `--dry-run`, and `init`
rejects a bad `--tools` before writing anything. (baseline-cli)

### Git is a precondition; `new` branches

`init` calls `require_repo` after parsing its options and before writing
anything, so a folder outside a repository is left untouched. `new` checks
everything that can refuse (repo, detached HEAD, existing branch) before
creating the change folder, then creates the folder and switches to the branch:
a refusal leaves neither. `--no-branch` skips the branch but still needs the
repo. `new` finds the base branch with `detect_base` and passes it to core, and
reports `branch` and `startedFrom` (`--json`, both `null` without a branch).
Commits and pushes stay in the skills, not in the CLI. (git-workflow)

### Modules are linked where the folder lives

`module add <path>` and `init <path>` both link the folder in the config of the
innermost module that contains it, wherever they run. Before writing anything,
both refuse a folder that holds a module (`held_module`): linking it would
leave that module listed past it, which loading refuses. Refusing was chosen
over moving the inner module's link, which would edit a config the user didn't
name. (module-add-nested)

### `init` writes the fixed layout

`init` always writes `.specworks/config.yml` (there is no `--dir`) and makes
`.specworks/changes/active/` and `.specworks/changes/archive/` with it, so the
two states of a change exist from the start; `module add` creates a module's
`.specworks/config.yml` the same way. Both refuse a folder that still holds an
old-style config, with the old-layout error and before writing anything; with
no project found, the "no project" message names `.specworks/config.yml`.
(active-changes-dir, move-config-into-spec-folder)

### Upgrading is uv, then `update`

`uv tool upgrade specworks` upgrades the CLI. `specworks update` then brings
the project's skills up to it, by default for the tools that already have
them installed. `context`, which every skill runs first, reports the skills
state and the hint `skills out of date: run specworks update`, so an agent
notices a stale project without being told. A self-upgrading `specworks
upgrade` was rejected: the CLI would have to find out how it was installed
and replace itself while running. Config migration will run in `update` once
a second config format exists. (upgrade-project)

## Interfaces

- `src/specworks/cli/__init__.py`: `app`, `main()` (the `specworks` entry
  point).
- `src/specworks/cli/output.py`: `emit`, `fail`, `workspace`,
  `resolve_change`, `resolve_archived`, `require_change`.
- `new <name> [--module M] [--no-branch] [--json]`: `--json` adds `branch` and
  `startedFrom`.
- The commands as `specworks --help` lists them: `version`, `init`, `skills`,
  `update`, `context`, `list`, `module add|list`, `capability add`, `new`, `status`,
  `abandon`, `phase`, `skip-specs`, `instructions`, `task list|done|undo`,
  `check`, `trace`, `spec show|list`, `diagrams`, `gate`, `start`, `review`,
  `cycle`, `validate`, `close`, `run`.

## Constraints

- No behaviour of its own beyond option handling, output and resolving
  references: the work belongs to the other capabilities.
