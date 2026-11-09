# Refinement: require-python-3-12

## Problem

The `harness` extra (chatinho, deepagents) needs Python 3.12+, but specworks still supports 3.11. That keeps environment markers on the extra and the dev group, a harness-less 3.11 CI job, a dead `sys.version_info` check in the `harness` command, and a `.python-version` of 3.11, so `uv run` builds a 3.11 venv where the harness tests are skipped. Raising the minimum to 3.12 removes all of it.

## Outcomes

- Installing specworks on Python 3.11 is refused by pip/uv with a "requires Python >=3.12" message.
- A fresh `uv sync` and `uv run` use Python 3.12+, so the harness tests run without extra flags.
- Every CI job tests and covers the harness; there is no 3.11 job.
- The docs say "Python 3.12+".
- `specworks harness` without the extra still fails, saying to install `specworks[harness]`, without naming a Python version (agreed: every supported Python is now 3.12+).

## Context

**Observed:**
- `pyproject.toml`: `requires-python = ">=3.11"`; the harness extra and the dev group carry `; python_version >= '3.12'` markers; ruff `target-version = "py311"`; mypy `python_version = "3.11"` with a comment about the 3.11 lint job.
- `.python-version` is `3.11`.
- `.github/workflows/ci.yml`: matrix `3.11`-`3.14`; coverage runs as two steps, one omitting `specworks/harness` on 3.11.
- `src/specworks/cli/harness.py`: `if sys.version_info < (3, 12): raise SpecworksError(EXTRA_MISSING)` (ruff UP036 flags it once the minimum is 3.12), and `EXTRA_MISSING` names Python 3.12.
- Docs that name 3.11 or 3.12: REQ-CLI-022 in `src/specworks/cli/docs/spec.md`, `src/specworks/cli/docs/design.md`, `src/specworks/harness/docs/design.md`, `CLAUDE.md`, `docs/architecture.md`, the project `context` in `.specworks/config.yml`, and docstrings in `src/specworks/harness/__init__.py` and `tests/harness/conftest.py`.
- `tests/cli/test_harness.py` (AC-CLI-022.1) asserts `"3.12"` in stderr.
- Capability `cli` owns REQ-CLI-022; `harness` has its own living docs.

**Assumed:**
- `uv.lock` regenerates cleanly under 3.12 (a previous trial run did, and the full suite passed on 3.12).
- The remaining CI jobs (3.12-3.14, macOS, Windows on 3.14) need no change beyond the matrix.
- The wheel smoke test does not depend on the Python minimum.

## Constraints

- [hard] CI runs `uv sync --locked`, so `uv.lock` must be regenerated and committed.
- [hard] Ruff UP036 flags the version check once the minimum is 3.12, so it must be removed.
- [hard] Living docs are written only by `specworks close`.
- [hard] CI keeps failing under 95% branch coverage, now including the harness on every job.
- [soft] Keep the diff to the places that name 3.11.

## Options

### Option A: Full bump

Set `requires-python = ">=3.12"`, drop the markers, set `.python-version` to 3.12, raise ruff and mypy targets, remove the 3.11 CI job and coverage split, remove the dead check, and update the wording and docs. REQ-CLI-022 and `EXTRA_MISSING` drop the Python version.

- **Pros:** meets every outcome; removes all stale 3.11 handling; one coverage path.
- **Cons:** largest diff; a spec change to REQ-CLI-022.
- **Effort:** S
- **Touches:** `cli`, `harness` (docs only), `integrations` unaffected
- **Outcomes:** meets all five.

### Option B: Minimal bump

Change only `requires-python`, `.python-version` and the CI matrix; leave markers, targets and the check in place.

- **Pros:** smallest diff; no spec change.
- **Cons:** dead markers and an obsolete check stay; ruff UP036 fails on the check; docs stay wrong.
- **Effort:** S
- **Touches:** none
- **Outcomes:** meets 1-3; fails 4 and 5.

### Option C: Bump and modernise to 3.12 idioms

Option A plus ruff `py312` with the UP rules applied across the code (for example the `type` statement and PEP 695 generics).

- **Pros:** the code uses the new minimum fully.
- **Cons:** unrelated churn and a larger review.
- **Effort:** M
- **Touches:** every capability
- **Outcomes:** meets all five, with unrequested changes.

## Recommendation

Option A (agreed with the user): it meets every outcome and removes the stale 3.11 handling without unrelated churn.

## Open Questions

- None.

## Candidate Capabilities

- `cli`: modified - REQ-CLI-022's error wording drops the Python version, and the dead version check goes.
- `harness`: modified - docs only (its design.md no longer says "On 3.11, coverage omits the package"); no behaviour change.
