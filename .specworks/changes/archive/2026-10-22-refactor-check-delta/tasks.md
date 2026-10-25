# Tasks: refactor-check-delta

## 1. Share the Issue helpers

- [x] 1.1 [code] Type `Issue.level` as `Literal["error", "warning"]` and add `Issue.error` / `Issue.warning` constructors in `src/specworks/specs/check.py`; verify `uv run mypy`
- [x] 1.2 [code] Replace every `Issue("error", ...)` / `Issue("warning", ...)` in `check.py` with the constructors and drop the `err` / `warn` closures; verify `specworks run test` and `specworks run lint`

## 2. Split `_check_delta`

- [x] 2.1 [code] Extract one function per concern (delta format, living-spec and capability registration, conflicts with other active changes, per-requirement ADDED / MODIFIED / REMOVED rules, requirement body) with the existing `@req` tags kept on the code they describe; verify `specworks run test`
- [x] 2.2 [code] Confirm the issues, messages and their order are unchanged: the tests pass with no edits to `tests/`, and coverage stays at or above 95% (`uv run coverage run -m pytest && uv run coverage report`)
