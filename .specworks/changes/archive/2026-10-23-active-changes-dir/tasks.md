# Tasks: active-changes-dir

## 1. Changes live in active/

- [x] 1.1 [test] Write failing tests tagged `@ac AC-PROJ-001.1`, `AC-PROJ-010.4`, `AC-PROJ-020.1`, `AC-PROJ-020.2`, `AC-PROJ-020.3` (a new change under `<dir>/changes/active/`, `active` refused, a loose folder not listed or found, a closed change in `archive/`); update the existing tests that spell `spec/changes/<name>` to `spec/changes/active/<name>`; verify the new ones fail for the right reason
- [x] 1.2 [code] Make `changes_path` the active folder and `archive_path` its sibling, stop `list_changes` skipping `archive`, and refuse `active` in `create_change` (REQ-PROJ-001, REQ-PROJ-010, REQ-PROJ-020) tagged `@req`; verify `uv run pytest`

## 2. init creates both folders

- [x] 2.1 [test] Write a failing test tagged `@ac AC-CLI-003.1` (`init` creates `<dir>/changes/active/` and `<dir>/changes/archive/`); update the `ready` line and `changesDir` assertions in `tests/test_cli.py` and `tests/test_modules.py`; verify it fails for the right reason
- [x] 2.2 [code] Make `init` create `active/` and `archive/` and print the active folder in its `ready` line (REQ-CLI-003) tagged `@req REQ-CLI-003`; verify `uv run pytest tests/test_cli.py tests/test_modules.py`

## 3. Text and paths

- [x] 3.1 [code] Change `spec/changes/` to `spec/changes/active/` in the `specworks-done` skill example, the config comments (`spec.yml`, `src/specworks/core/config_file.py`) and the CI smoke test; run `uv run specworks skills` to refresh the installed copies (REQ-PROJ-020); verify with `grep -rn "spec/changes/[a-z]" src .github spec.yml` showing no loose path
- [x] 3.2 [code] Last: move this change with `git mv spec/changes/active-changes-dir spec/changes/active/active-changes-dir` and verify `uv run specworks status --change active-changes-dir` and `uv run pytest` (REQ-PROJ-020)

## Workflow follow-up

- The GitHub wiki says `spec/changes/` in its text; update it after this lands.
