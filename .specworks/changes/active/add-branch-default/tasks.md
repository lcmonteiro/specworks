# Tasks: add-branch-default

## 1. The branch setting

- [x] 1.1 Add the stubs in design.md's Interfaces: `Config.branch_per_change` (always `True`) with the key in `CONFIG_KEYS`, `branch_per_change` in `SETTABLE_KEYS`, and `current_branch` in `src/specworks/core/git.py` returning `None` (REQ-PROJ-026, REQ-PROJ-025, REQ-CLI-015); verify `specworks run lint` passes
- [x] 1.2 [test] Tests for AC-PROJ-026.1 to AC-PROJ-026.4 (the default and `init`'s text naming the key, `false` loaded, `sometimes` refused with the pinned message, a module's own value ignored through `ws.top`) and AC-PROJ-025.12 (`false` written as one line on the default config, `maybe` refused with the pinned message and the file unchanged), tagged `@ac`; verify they fail on the stubs
- [x] 1.3 [code] Implement the key's load check, the `DEFAULT_CONFIG` block and `set_config_value` for `branch_per_change` as design.md decides, tagged `@req REQ-PROJ-026` / `@req REQ-PROJ-025`; verify `specworks run lint` passes and, in a scratch project, `specworks config set branch_per_change false` leaves `branch_per_change: false` in the config and `specworks context` still loads

## 2. new

- [x] 2.1 Change `new`'s flag to `--branch/--no-branch` (default `None`) and add `stayedOn` to its JSON as `null`, as stubs (REQ-CLI-015); verify `specworks new --help` shows `--branch / --no-branch`
- [x] 2.2 [test] Tests for AC-CLI-015.1 to AC-CLI-015.5 in a temporary git repository (the setting false stays with `stayedOn` naming the branch; `--branch` overrides false; `--no-branch` overrides the default; no setting and no flag creates the branch with `stayedOn` null; the text line `stayed on work`), tagged `@ac`; verify they fail on the stubs
- [x] 2.3 [code] Implement `current_branch` and `new` as design.md decides (the setting from `ws.top.config`, the flags, `stayedOn`, the text line), tagged `@req REQ-CLI-015`; verify `specworks run lint` passes and, in a scratch repository with `branch_per_change: false`, `specworks new demo --json` prints `"branch": null` and `"stayedOn"` naming the checked-out branch

## 3. Review cycle 1

- [x] 3.1 [test] Review R2: a test for AC-CLI-013.6 (`config set branch_per_change false --json` inside `billing`'s folder and with `--module billing` writes the top level's config, billing's config unchanged, the output naming the top level's config), tagged `@ac`; and Review R1: the existing AC-CLI-006.1 to AC-CLI-006.9 tests (REQ-CLI-006, reworded to name `branch_per_change`) still pass unchanged; verify the new test fails before 3.2
- [x] 3.2 [code] Review R2 and R3: `config set` writes `branch_per_change` to the top level's config whatever the target module, and its key help and docstring name `branch_per_change` (REQ-CLI-013); and Review R1: tag `new` with `@req REQ-CLI-006` next to REQ-CLI-015 if missing (REQ-CLI-006, no behaviour change), tagged `@req`; verify `specworks run lint` passes and, in a scratch project with a module, `specworks config set branch_per_change false --module <m> --json` names `.specworks/config.yml`

## 4. Review cycle 2

- [ ] 4.1 [test] Review R4: a test for AC-CLI-015.6 (`branch_per_change: false` with a detached HEAD: `new add-login --json` creates the change, HEAD stays detached, `branch` and `stayedOn` null), tagged `@ac`; and the existing AC-CLI-006.8 test still passes as reworded (REQ-CLI-006); verify it passes on the current code
