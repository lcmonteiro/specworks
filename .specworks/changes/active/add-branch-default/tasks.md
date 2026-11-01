# Tasks: add-branch-default

## 1. The branch setting

- [x] 1.1 Add the stubs in design.md's Interfaces: `Config.branch_per_change` (always `True`) with the key in `CONFIG_KEYS`, `branch_per_change` in `SETTABLE_KEYS`, and `current_branch` in `src/specworks/core/git.py` returning `None` (REQ-PROJ-026, REQ-PROJ-025, REQ-CLI-015); verify `specworks run lint` passes
- [x] 1.2 [test] Tests for AC-PROJ-026.1 to AC-PROJ-026.4 (the default and `init`'s text naming the key, `false` loaded, `sometimes` refused with the pinned message, a module's own value ignored through `ws.top`) and AC-PROJ-025.12 (`false` written as one line on the default config, `maybe` refused with the pinned message and the file unchanged), tagged `@ac`; verify they fail on the stubs
- [ ] 1.3 [code] Implement the key's load check, the `DEFAULT_CONFIG` block and `set_config_value` for `branch_per_change` as design.md decides, tagged `@req REQ-PROJ-026` / `@req REQ-PROJ-025`; verify `specworks run lint` passes and, in a scratch project, `specworks config set branch_per_change false` leaves `branch_per_change: false` in the config and `specworks context` still loads

## 2. new

- [x] 2.1 Change `new`'s flag to `--branch/--no-branch` (default `None`) and add `stayedOn` to its JSON as `null`, as stubs (REQ-CLI-015); verify `specworks new --help` shows `--branch / --no-branch`
- [x] 2.2 [test] Tests for AC-CLI-015.1 to AC-CLI-015.5 in a temporary git repository (the setting false stays with `stayedOn` naming the branch; `--branch` overrides false; `--no-branch` overrides the default; no setting and no flag creates the branch with `stayedOn` null; the text line `stayed on work`), tagged `@ac`; verify they fail on the stubs
- [ ] 2.3 [code] Implement `current_branch` and `new` as design.md decides (the setting from `ws.top.config`, the flags, `stayedOn`, the text line), tagged `@req REQ-CLI-015`; verify `specworks run lint` passes and, in a scratch repository with `branch_per_change: false`, `specworks new demo --json` prints `"branch": null` and `"stayedOn"` naming the checked-out branch
