# Design: cli

## Overview

The `specworks` command line (Typer) in `src/specworks/cli`. It is a thin layer:
each command resolves the workspace and the change, calls the capability that
does the work (`project`, `specs`, `workflow`, `integrations`), and prints the
result as text or JSON.
- `app.py`: the Typer app and its command groups (`module`, `spec`, `task`,
  `capability`, `finding`).
- `output.py`: the shared options, output, errors, and resolving the workspace
  and changes.
- `project.py`: `init`, `skills`, `context`, `list`, `module`, `capability`.
- `changes.py`: `new`, `status`, `abandon`, `phase`, `skip-specs`,
  `instructions`, `task`.
- `specs.py`: `check`, `trace`, `spec`, `diagrams`.
- `workflow.py`: `gate`, `start`, `review`, `finding`, `cycle`, `merge`,
  `validate`, `close`, `run`.
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
rejects a bad `--tools` (given or typed at its question) before writing
anything. (baseline-cli, dedupe-copilot-skills)

### The tools are chosen once and saved

`init`, `skills` and `update` call `resolve_tools` and save the result in the
config with `save_tools` when it says to. `--tools` defaults to `None`, not
`auto`, so "not given" can be told from an explicit `auto`. When `init`
installs skills at a top level with no `--tools` and no saved tools, and
`is_terminal()` (`sys.stdin.isatty()`, its own function so tests can replace
it) is true, it asks once, before writing anything, with `typer.prompt`:
`AI tools to install skills for (claude, copilot)`, the detected tools as the
default comma list. The answer goes through `parse_tools`. Without a terminal
it uses `auto`, so scripts and agents are never blocked. A checklist widget was
rejected: the question is one line of text. (dedupe-copilot-skills)

### Git is a precondition; `new` branches

`init` calls `require_repo` after parsing its options and before writing
anything, so a folder outside a repository is left untouched. `new` checks
everything that can refuse (repo, detached HEAD, existing branch) before
creating the change folder, then creates the folder and switches to the branch:
a refusal leaves neither. `--no-branch` skips the branch but still needs the
repo. `new` finds the base branch with `detect_base` and passes it to core, and
reports `branch` and `startedFrom` (`--json`, both `null` without a branch).
Commits and pushes stay in the skills, not in the CLI, except the merge
commit `merge` makes when it joins a half's branch. (git-workflow,
merge-halves-without-conflicts)

### Findings are written through `finding`, not by hand

`specworks finding add|decide|done|close` write a change's review.md through
the `workflow` writers, so the skills never edit it by hand and a malformed
line is refused when it is written, not when `gate review` runs. A
`FindingError` reaches the `App` wrapper like any other error. Under `--json`
each prints the change, the finding as `specworks cycle` sees it plus
`done`, and `path` (review.md); `done` is added here rather than to
`Finding.to_dict()`, so `cycle`'s output is unchanged. (finding-commands)

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
the project's skills up to it, by default for the saved tools, else those that
already have them installed (then saved), and removes the copies no longer
needed. `context`, which every skill runs first, reports the skills
state and the hint `skills out of date: run specworks update`, so an agent
notices a stale project without being told. A self-upgrading `specworks
upgrade` was rejected: the CLI would have to find out how it was installed
and replace itself while running. Config migration will run in `update` once
a second config format exists. (upgrade-project, dedupe-copilot-skills)

## Interfaces

- `src/specworks/cli/__init__.py`: `app`, `main()` (the `specworks` entry
  point).
- `src/specworks/cli/output.py`: `emit`, `fail`, `workspace`,
  `resolve_change`, `resolve_archived`, `require_change`, `ToolsOpt`
  (`--tools`, default `None`: the saved choice).
- `src/specworks/cli/project.py`: `is_terminal() -> bool`.
- `new <name> [--module M] [--no-branch] [--json]`: `--json` adds `branch` and
  `startedFrom`.
- The commands as `specworks --help` lists them: `version`, `init`, `skills`,
  `update`, `context`, `list`, `module add|list`, `capability add`, `new`, `status`,
  `abandon`, `phase`, `skip-specs`, `instructions`, `task list|done|undo`,
  `check`, `trace`, `spec show|list`, `diagrams`, `gate`, `start`, `review`,
  `finding add|decide|done|close`, `cycle`, `merge`, `validate`, `close`, `run`.
- `finding add TYPE TEXT --proposal TEXT`, `finding decide ID DECISION`,
  `finding done ID TEXT --in STEP`, `finding close ID TEXT`, each with
  `--change <ref> [--json]`: `--json` prints the change's fields plus
  `finding` (`id`, `type`, `text`, `phase`, `doneIn` when set, `done`) and
  `path` (review.md, workspace-relative); text output is
  `<id> <type> -> <phase> (open|done)` and the path.
- `merge <branch> --change <ref> [--json]`: `--json` prints the change's
  fields plus `merged`, `branch` and `resolved` (workspace-relative paths).

## Constraints

- No behaviour of its own beyond option handling, output and resolving
  references: the work belongs to the other capabilities.
