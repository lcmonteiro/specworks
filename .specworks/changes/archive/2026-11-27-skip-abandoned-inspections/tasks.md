# Tasks: skip-abandoned-inspections

## 1. Abandoned changes show no inspection notes (cli)

- [x] 1.1 [test] Write failing tests in `tests/cli/` for AC-CLI-025.4, AC-CLI-026.2 and AC-CLI-027.4 (an abandoned change made with `specworks abandon`, its archived inspection.md given an open I1), tagged `@ac`; verify they fail on the `inspection` key or the `inspected` entry
- [x] 1.2 [code] Make `inspection_dict` return `{}` for an abandoned change (REQ-CLI-025, REQ-CLI-026) tagged `@req REQ-CLI-025` and `@req REQ-CLI-026`; verify `uv run ruff check src && uv run mypy`
- [x] 1.3 [code] Build `context`'s `inspected` from the archived changes whose `inspection_dict` is not empty (REQ-CLI-027) tagged `@req REQ-CLI-027`; verify `uv run specworks context --json` still has `"inspected": []` here
