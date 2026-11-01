# Design: add-branch-default

## Context

`new` (`src/specworks/cli/changes.py`) creates the change, then its branch
unless `--no-branch`. Top-level-only settings are read from
`ws.top.config` (as `diagrams` is). `set_config_value`
(`src/specworks/core/config_file.py`) edits `context` and `commands.<key>`
as text with a reload check. See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- One top-level key that `new` follows, with flags to override it once.
- `config set` writes it the same checked way.

**Non-Goals:**
- An environment variable; a different default; the branch's name or start.

## Decisions

### The key

`branch_per_change` joins `CONFIG_KEYS`. `Config.branch_per_change: bool =
True`. A value that is not a YAML boolean is refused at load with
`'branch_per_change' must be true or false`. Every module's config may carry
it (it loads), but only `ws.top.config.branch_per_change` is read, as for
`diagrams`. Serves: REQ-PROJ-026.

### The default config

`DEFAULT_CONFIG` gains, after `docs_dir`, a commented block:

```
# Whether `specworks new` creates and switches to a branch for each change
# (true, the default). Set it to false to stay on the current branch, e.g.
# when the branch is chosen for you; `new --branch` / `--no-branch` override it.
# branch_per_change: false
```

The key stays unset, so the default is `true`. Serves: REQ-PROJ-026.

### Setting it

`SETTABLE_KEYS` becomes `context`, `commands.<key>`..., `branch_per_change`.
For `branch_per_change` the value must be `true` or `false` (exactly, case
sensitive), else `branch_per_change must be true or false` before reading
the file. An uncommented top-level line `branch_per_change:` is replaced by
`branch_per_change: <value>`; otherwise a blank line and that line are
appended. The check after writing is the same as for the other keys, with
the expected value the boolean. An empty value is refused like any other
non-boolean (clearing would mean "default", which is `true`; set `true`
instead). Serves: REQ-PROJ-025.

### `new`

The flag becomes `--branch/--no-branch` with default `None`
(`branch: bool | None`). The branch is created when `branch` is true, or
when it is `None` and `ws.top.config.branch_per_change` is true. When it
stays, `stayedOn` is the current branch (`symbolic-ref --short HEAD`), or
null on a detached HEAD; it is null when a branch was created. Text: a line
`stayed on <branch>` after `created <path>` when `stayedOn` is set. A new
helper `current_branch(cwd) -> str | None` in `src/specworks/core/git.py`
reads it. `require_repo` still runs first, so a folder outside git is still
refused as today. Serves: REQ-CLI-015.

### Pinned wording

Messages and text the tests assert, verbatim:

- load error: `'branch_per_change' must be true or false`
- `config set` error: `branch_per_change must be true or false`
- the `new` text line: `stayed on <branch>`
- `DEFAULT_CONFIG` contains `# branch_per_change: false`

## Interfaces

- `src/specworks/core/config.py`: `Config.branch_per_change: bool = True`;
  `"branch_per_change"` in `CONFIG_KEYS` (REQ-PROJ-026).
- `src/specworks/core/config_file.py`: `"branch_per_change"` in
  `SETTABLE_KEYS`; `set_config_value(root, "branch_per_change", "true"|"false")`
  (REQ-PROJ-025); the block in `DEFAULT_CONFIG` (REQ-PROJ-026).
- `src/specworks/core/git.py`: `current_branch(cwd: Path) -> str | None`
  (REQ-CLI-015).
- `src/specworks/cli/changes.py`: `new(..., branch: bool | None = typer.Option(None, "--branch/--no-branch", ...))`;
  JSON gains `stayedOn: str | None` (REQ-CLI-015).

## Diagrams

No structural change: a key, a helper and an option on existing modules.

## Risks / Trade-offs

- [`--no-branch` was a plain flag; `--branch/--no-branch` keeps that
  spelling working] -> AC-CLI-015.3 checks it.
- [a project sets `false` in a module expecting it to apply there] -> the
  default config's comment and REQ-PROJ-026 say only the top level counts.

## Open Questions

None.
