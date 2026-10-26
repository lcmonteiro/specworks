# Review: colour-safe-cli-tests

Base: `origin/main`

## Findings

None.

The change is `skip-specs` (tests only), so it was read against the
proposal, design.md's Decision and tasks.md:
- `tests/conftest.py:6`: the autouse `plain_output` fixture sets `TERM=dumb`
  with `monkeypatch.setenv`, as the Decision says; nothing in `src/` changed.
- `tests/test_cli.py:370`: the guard test sets `GITHUB_ACTIONS=true` and
  `FORCE_COLOR=1`, and asserts exit 2, no `\x1b` and
  `No such option: --dir`. Without `TERM=dumb` the same invocation writes
  ANSI codes and the text check fails, so the test would catch a regression.
- `tests/test_cli.py:366` (`test_init_has_no_dir_option`, AC-CLI-003.8):
  the ANSI strip is gone and the assertion is unchanged; `re` is still used
  elsewhere in the file.
- The suite passes with and without `GITHUB_ACTIONS=true FORCE_COLOR=1`
  (620 tests), and `ruff check` passes. No other test sets `TERM` or checks
  coloured output, so the proposal's assumption holds.

## Changed files without tags

- `tests/conftest.py`: test setup (a fixture), not a test of any criterion;
  the change is `skip-specs`.

## Summary

No drift: the code follows the proposal and the design's one Decision, the
guard test fails without the fixture, and the suite passes under CI's colour
settings. No change to code, specs or design; nothing sent back.
