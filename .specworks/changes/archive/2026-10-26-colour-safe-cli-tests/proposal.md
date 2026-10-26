# Proposal: colour-safe-cli-tests

## Why

CI's colour codes split CLI text such as `--dir` in typer's error boxes, so
a test that matches CLI output can pass locally and fail on every CI runner,
as on PR #82. The refinement chose Option A: plain output for the whole test
run, set once in `tests/conftest.py`.

## What Changes

- `tests/conftest.py`: an autouse fixture sets `TERM=dumb` for every test,
  so every `CliRunner` writes plain text even when `GITHUB_ACTIONS=true` or
  `FORCE_COLOR=1` is set.
- A guard test: with `GITHUB_ACTIONS=true` and `FORCE_COLOR=1` set, a CLI
  usage error (`init --dir`) has no ANSI escape codes.
- `tests/test_cli.py::test_init_has_no_dir_option` matches the output
  directly again; its one-off ANSI strip is removed.
- Assumption: no test checks coloured output on purpose.

## Capabilities

None: tests only; the change is marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- `tests/conftest.py`, `tests/test_cli.py`. No change to `src/`, the CLI's
  output, or CI config.

## Out of Scope

- Changing how the CLI itself decides on colour.
- A per-test `plain()` helper or CI-only settings.
