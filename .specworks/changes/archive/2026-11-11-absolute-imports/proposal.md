# Proposal: absolute-imports

## Why

The package code in `src/specworks` imports its own modules with relative
paths (`from ..core.changes import ...`), while the tests use
`specworks.core.changes`. Relative paths are harder to read and grep, and
nothing keeps new ones out (refinement.md, Option A).

## What Changes

- Every relative import in `src/specworks` (214 lines in 55 files, including
  the two lazy imports inside functions) becomes an absolute
  `from specworks.<...> import ...`, rewritten by ruff's `TID252` fix.
- `pyproject.toml` enables ruff's `TID` rules with
  `[tool.ruff.lint.flake8-tidy-imports] ban-relative-imports = "all"`, so
  `specworks run lint` and CI's lint job fail on any new relative import.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None: no behaviour changes. Only import lines of every capability's code
(`project`, `specs`, `workflow`, `integrations`, `cli`, `harness`) and the
lint config change, so the change is marked `skip-specs`.

## Related requirements

- REQ-PROJ-003 left: checks the `commands` config values, not import style.
- REQ-PROJ-007 left: which commands a module inherits.
- REQ-PROJ-013 left: running the configured commands, lint among them.
- REQ-PROJ-025 left: setting a command in the config.
- REQ-PROJ-034 left: the reopen record (a lint failure is only its example).
- REQ-SPECS-015 left: how a code task is verified.
- REQ-FLOW-008 left: gate code runs the configured lint command, whatever it checks.
- REQ-FLOW-013 left: validate runs the configured lint command.
- REQ-CLI-020, REQ-CLI-021, REQ-CLI-022 left: the `reopen` command surface; "lint" appears only in examples.

## Impact

- Code: import lines of 55 files under `src/specworks`; no logic change.
- Config: `pyproject.toml` (`[tool.ruff.lint]`).
- Dependencies: none (ruff is already a dev dependency).
- Contributors: a relative import in `src/` or `tests/` now fails lint.

## Out of Scope

- The tests, which already import `specworks...`.
- Reordering or regrouping imports beyond what ruff's `I` rule does after
  the rewrite.
- A written convention in `CLAUDE.md` (the lint rule is the convention).
