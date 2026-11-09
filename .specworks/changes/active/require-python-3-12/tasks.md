# Tasks: require-python-3-12

## 1. The missing-extra message

- [x] 1.1 [test] Change the AC-CLI-022.1 test in `tests/cli/test_harness.py` to expect `specworks[harness]` in stderr and no Python version, tagged `@ac AC-CLI-022.1` (REQ-CLI-022, AC-CLI-022.1); verify it fails against the current message
- [ ] 1.2 [code] In `src/specworks/cli/harness.py` remove the `sys.version_info` check and its `import sys`, and drop the Python version from `EXTRA_MISSING` and the command docstring, tagged `@req REQ-CLI-022` (REQ-CLI-022); verify `uv run ruff check src` and `uv run mypy`

## 2. Packaging and tooling

- [ ] 2.1 [code] In `pyproject.toml` set `requires-python = ">=3.12"`, drop the `python_version >= '3.12'` markers from the harness extra and the dev group, set ruff `target-version = "py312"` and mypy `python_version = "3.12"` and remove its 3.11 comment; set `.python-version` to 3.12 and regenerate `uv.lock` (refinement outcomes 1 and 2, no REQ); verify `uv lock --check` and `uv run ruff check src tests`
- [ ] 2.2 [code] In `.github/workflows/ci.yml` drop `"3.11"` from the matrix and the harness-less coverage step, run `uv run coverage report` for every job and fix the comments (refinement outcome 3, no REQ); verify the file parses with `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` or by inspection

## 3. Docs

- [ ] 3.1 [code] Say "Python 3.12+" in `CLAUDE.md`, `docs/architecture.md`, the `context` in `.specworks/config.yml`, and the docstrings in `src/specworks/harness/__init__.py` and `tests/harness/conftest.py`; the living docs under `src/specworks/*/docs/` are left to close (refinement outcome 4, no REQ); verify `grep -rn "3\.11" CLAUDE.md docs .specworks/config.yml src/specworks/harness/__init__.py tests/harness/conftest.py` finds nothing
