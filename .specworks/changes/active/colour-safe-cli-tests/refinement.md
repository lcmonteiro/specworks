# Refinement: colour-safe-cli-tests

## Problem

Tests that match CLI output pass locally and fail on CI when the output
carries colour codes. On PR #82 every test job failed because typer's
error box split `--dir` with ANSI codes, so `"No such option: --dir"` was
not found. That one test now strips the codes itself, but any new test that
matches CLI text has the same trap.

## Context

**Observed:**
- Every test file makes its own `CliRunner()` (`tests/helpers.py`,
  `tests/test_cli.py`, `tests/test_modules.py` and seven more);
  `tests/conftest.py` holds only fixtures.
- CI sets `GITHUB_ACTIONS=true`, which makes rich force colour in typer's
  output; reproduced locally with `GITHUB_ACTIONS=true`.
- `NO_COLOR=1` is not enough: rich still writes bold codes, which still split
  `--dir`.
- `TERM=dumb` gives plain output even with `GITHUB_ACTIONS=true` and
  `FORCE_COLOR=1`; so does typer's private `_TYPER_FORCE_DISABLE_TERMINAL=1`.
- Only `tests/test_cli.py::test_init_has_no_dir_option` strips ANSI codes
  today (added for PR #82).

**Assumed:**
- No test checks coloured output on purpose (only that one test mentions
  `\x1b`).

## Constraints

- [hard] No behaviour change: tests and test setup only (`skip-specs`).
- [hard] The suite passes with `GITHUB_ACTIONS=true FORCE_COLOR=1` set, as on
  CI, and without them.
- [soft] Prefer a public convention over typer's private flag.

## Options

### Option A: plain output for the whole test run, in conftest

An autouse fixture in `tests/conftest.py` sets `TERM=dumb` for every test,
so every `CliRunner` gets plain text whatever the shell or CI sets. The
one-off strip in the PR #82 test is removed.

- **Pros:** one place; nothing for a new test to remember; public
  convention.
- **Cons:** a test that wants colour would have to opt back in (none does).
- **Effort:** S
- **Touches:** tests only

### Option B: a shared `plain(output)` helper

- **Pros:** explicit at each use.
- **Cons:** every new test must remember it, which is how PR #82 broke.
- **Effort:** S
- **Touches:** tests only

### Option C: set the variable in CI only

- **Pros:** one line in `.github/workflows/ci.yml`.
- **Cons:** a contributor with `FORCE_COLOR=1`, or another CI, still breaks.
- **Effort:** S
- **Touches:** CI config

## Recommendation

Option A, chosen by the user: `TERM=dumb` for every test from
`tests/conftest.py`, and the per-test strip removed.

## Open Questions

None.

## Candidate Capabilities

- None: tests only (`skip-specs`).
