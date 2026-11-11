# Refinement: absolute-imports

## Problem

The package code in `src/specworks` imports its own modules with relative paths
(`from ..core.changes import ...`, `from .base import ...`, `from . import ...`),
while the tests import the same modules as `specworks.core.changes`. Relative
paths are harder to read and grep, and their meaning depends on where the file
sits. Nothing keeps new ones out, so the mix would persist.

## Outcomes

- Every import of specworks' own modules in `src/` reads `from specworks.<...>`;
  none is relative.
- `specworks run lint` (and CI's lint job) fails on any new relative import.
- The tests, the CLI and the installed wheel behave exactly as before.

## Context

**Observed:**
- `src/` has 214 relative import lines in 55 files and no absolute
  `specworks` import. ruff's `TID252` counts 478 relative names (one per
  imported name).
- Two relative imports are inside functions: the lazy import of the optional
  harness, which `docs/architecture.md` ("Optional capabilities are imported
  lazily") requires to stay lazy.
- `tests/` already imports `specworks...` everywhere (160 imports).
- `pyproject.toml` selects ruff rules `E4, E7, E9, F, I, B, UP`, with no
  `TID`. The rule groups imports into stdlib, third party and specworks
  (`src = ["src", "tests"]`).
- ruff can rewrite them (`TID252` with `ban-relative-imports = "all"`), but it
  marks the fix as unsafe, so it has to be applied explicitly
  (`--unsafe-fixes`).
- Every capability's code is touched (`project`, `specs`, `workflow`,
  `integrations`, `cli`, `harness`), but none of their behaviour.

**Assumed:**
- The package is always imported as `specworks` (the installed wheel, `uv run`
  and the tests), so absolute imports resolve the same as relative ones.
- Rewriting the imports creates no import cycle that the relative form hid.
  Both forms load the same modules in the same order.

## Constraints

- [hard] No behaviour change: the tests, ruff, mypy and the 95% branch
  coverage stay green on every CI platform.
- [hard] The harness import stays inside its function, so specworks works
  without the extra installed.
- [soft] Import order and grouping change only where ruff's `I` rule moves the
  rewritten lines; no other reshuffling.
- [soft] No behaviour change, so the change is likely `skip-specs` (no
  requirement or acceptance criterion to add).

## Options

### Option A: Rewrite and enforce

Run ruff's `TID252` fix once over `src/`, and enable `TID` in
`pyproject.toml` with `[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"`.

- **Pros:** one mechanical rewrite; the existing lint command and CI keep
  relative imports out for good.
- **Cons:** a large diff (55 files), but only in import lines.
- **Effort:** S
- **Touches:** every capability's code (imports only), `pyproject.toml`
- **Outcomes:** meets all three.

### Option B: Rewrite and document

The same one-time rewrite, plus a line in `CLAUDE.md`'s Conventions, with no
lint rule.

- **Pros:** no lint config change.
- **Cons:** nothing checks the convention; relative imports can come back.
- **Effort:** S
- **Touches:** every capability's code (imports only), `CLAUDE.md`
- **Outcomes:** meets 1 and 3, fails 2.

### Option C: Rewrite only

The same one-time rewrite, with neither a lint rule nor a documented
convention.

- **Pros:** the smallest change.
- **Cons:** the convention is neither written down nor checked.
- **Effort:** S
- **Touches:** every capability's code (imports only)
- **Outcomes:** meets 1 and 3, fails 2.

## Recommendation

Option A, agreed with the user: one rewrite with ruff, then the lint rule
enforces it, with no new check to maintain.

## Open Questions

- None blocking. Whether to mark the change `skip-specs` is decided in
  `/specworks-specify` (who can answer: the user).

## Candidate Capabilities

- None: no capability's behaviour changes. The rewrite touches the code of
  `project`, `specs`, `workflow`, `integrations`, `cli` and `harness`, but only
  their import lines.
