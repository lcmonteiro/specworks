# Design: absolute-imports

## Context

See proposal.md. Every capability's code is touched, but only its import
lines; ruff already lints `src` and `tests` (`specworks run lint`).

## Goals / Non-Goals

- Goal: no relative import left in `src/specworks`, and lint keeps it so.
- Non-goal: any change to what is imported, or when.

## Decisions

- **ruff rewrites, by hand nothing.** `uv run ruff check src --select TID252
  --fix --unsafe-fixes` turns each relative import into its absolute form
  (ruff marks the fix unsafe only because it cannot prove the package root;
  here it is always `specworks`). Then `uv run ruff check src --fix` lets the
  `I` rule regroup the rewritten lines with the other `specworks` imports.
  Alternative: a sed rewrite, rejected (it would get `from . import x` and
  multi-dot paths wrong).
- **Enforced with `TID252`.** `pyproject.toml` adds `"TID"` to
  `[tool.ruff.lint] select` and `[tool.ruff.lint.flake8-tidy-imports]
  ban-relative-imports = "all"` (the default, `"parents"`, would still allow
  `from .base import`). Alternative: a convention in `CLAUDE.md` only,
  rejected in refinement (nothing checks it).
- **Lazy imports stay lazy.** The two indented imports are rewritten in
  place and stay where they are. `src/specworks/cli/harness.py`'s
  `from specworks.harness import run_harness` stays inside `harness()`, the
  lazy import docs/architecture.md requires, so `import specworks` still
  works without the harness extra. `src/specworks/harness/workspaces.py`'s
  `from specworks.harness.backend import GitBackend` stays under
  `if TYPE_CHECKING:` at module level: it is type-only and never runs at
  import time.

## Interfaces

None: no public API, data shape or CLI surface changes.

## Diagrams

No structural change.

## Risks / Trade-offs

- A large diff (55 files) that conflicts with any branch touching the same
  imports: the change is merged quickly and on its own.
- An absolute import could hide a cycle the relative one did not: both load
  the same modules in the same order, and the full test suite runs in review.

## Open Questions

None.
