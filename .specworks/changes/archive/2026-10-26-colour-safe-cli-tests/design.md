# Design: colour-safe-cli-tests

## Context

Every test file makes its own `CliRunner()`; `tests/conftest.py` holds only
the `project` and `repo` fixtures. With `GITHUB_ACTIONS=true` (as on CI) rich
forces colour in typer's output, and its codes split text such as `--dir`.
`TERM=dumb` turns that off even with `FORCE_COLOR=1` set (see refinement.md).

## Goals / Non-Goals

**Goals:**
- Every test sees plain CLI output, whatever the shell or CI sets.

**Non-Goals:**
- Changing how the CLI itself decides on colour.

## Decisions

### `TERM=dumb` from an autouse fixture in `tests/conftest.py`

The fixture uses `monkeypatch.setenv("TERM", "dumb")`, so it is undone after
each test and applies to every `CliRunner` without each test remembering it.
Alternatives (a `plain()` helper, a CI-only variable, typer's private
`_TYPER_FORCE_DISABLE_TERMINAL`) were rejected in the refinement.

## Interfaces

None: the change touches test setup only (`skip-specs`); no public API, CLI
surface or data shape in `src/` is added or changed, so there are no stubs.

## Risks / Trade-offs

- [a future test wants coloured output] -> it overrides `TERM` with its own
  `monkeypatch.setenv`.
