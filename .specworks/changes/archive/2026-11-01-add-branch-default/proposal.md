# Proposal: add-branch-default

## Why

`specworks new` always switches to a new branch unless `--no-branch` is
passed, and no skill passes it. A project whose branch is already chosen
needs to say so once, in its config, instead of relying on the agent
remembering a flag on every change.

## What Changes

- New top-level config key `branch_per_change: true|false` (default `true`;
  a module's own value is ignored). Any other value is refused at load.
- `specworks new` reads it: `false` stays on the current branch. New
  `--branch` forces a branch; `--no-branch` keeps staying. When it stays,
  the output says `stayed on <branch>` and `--json` has `stayedOn`.
- `specworks config set branch_per_change true|false` writes it.
- The default config written by `init` describes the key (commented out).

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `project`: adds REQ-PROJ-026 (the `branch_per_change` key); modifies
  REQ-PROJ-025 (it can also be set with `set_config_value`).
- `cli`: adds REQ-CLI-015 (`new` stays or branches as the setting and flags
  say).

## Impact

- `src/specworks/core/config.py`: the key, its check, `Config` and the
  workspace's value.
- `src/specworks/core/config_file.py`: `DEFAULT_CONFIG`, `SETTABLE_KEYS`,
  `set_config_value`.
- `src/specworks/cli/changes.py`: `new`'s `--branch/--no-branch` and output.
- No change to the branch's name or start point (REQ-PROJ-018/019).

## Out of Scope

- An environment variable.
- Changing the default (still one branch per change).
- Setting the key in this repository's own config.
