# Tasks: absolute-imports

## 1. Enforce absolute imports

- [x] 1.1 [code] In `pyproject.toml`, add `"TID"` to `[tool.ruff.lint] select` and a `[tool.ruff.lint.flake8-tidy-imports]` table with `ban-relative-imports = "all"`; verify `uv run ruff check src --select TID252` now reports the existing relative imports

## 2. Rewrite the relative imports

- [x] 2.1 [code] Run `uv run ruff check src --select TID252 --fix --unsafe-fixes`, then `uv run ruff check src --fix` to regroup them; verify `grep -rnE "^\s*from \.+" src` prints nothing and `specworks run lint` passes
- [x] 2.2 [code] Check that the lazy imports in `src/specworks/cli/harness.py` and `src/specworks/harness/workspaces.py` are still inside their functions; verify by reading both files
