# Design: require-python-3-12

## Context

`specworks harness` guarded itself twice: a `sys.version_info < (3, 12)` check, and a `try`/`except ImportError` around the import of `specworks.harness`. With `requires-python >=3.12` the first can never fire (ruff UP036 flags it), so only the import guard remains. See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- `harness.py` keeps one guard, the lazy import, and its error names only the extra.

**Non-Goals:**
- Any change to the harness behaviour, or to how other commands avoid importing it (REQ-CLI-022).

## Decisions

### Keep the lazy import guard, drop the version check

The import stays inside the command's body so `import specworks` and every other command never load chatinho or deepagents. The `ImportError` still raises `SpecworksError("specworks harness needs the harness extra: install specworks[harness]")`. Alternative: keep the check as a safety net. Rejected: pip and uv refuse older Pythons before specworks can run, and ruff flags it as dead code. Serves: REQ-CLI-022.

## Interfaces

None. `EXTRA_MISSING` in `src/specworks/cli/harness.py` changes text only.

## Diagrams

No structural change.

## Risks / Trade-offs

- [Users on 3.11 are locked out of the next release] -> **BREAKING** is stated in the proposal; the previous release keeps working on 3.11.
- [`uv.lock` out of date makes `uv sync --locked` fail in CI] -> regenerate it with `uv lock` and check it with `uv lock --check`.

## Migration / Rollback

Users on 3.11 stay on the previous release or move to 3.12+. Rollback is reverting `requires-python` and the markers.
