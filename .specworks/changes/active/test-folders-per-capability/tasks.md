# Tasks: test-folders-per-capability

## 1. Split the tests

- [x] 1.1 [code] Move each tagged test to `tests/<capability>/test_<topic>.py` by its first tag's capability, untagged tests staying in `tests/test_<topic>.py`, and helpers shared across capabilities to `tests/support/<topic>.py` (shared fixtures as `make_<name>` behind a one-line fixture); verify each capability folder holds only its own prefix's tags
- [x] 1.2 [code] Run pytest with `--import-mode=importlib` and `pythonpath = ["tests"]` in `pyproject.toml`; verify the collected test IDs (without their folder) equal those before the split

## 2. Config and docs

- [x] 2.1 [code] Set `commands.test_scoped: uv run pytest {paths}` and name the layout in the context of `.specworks/config.yml`; verify `specworks context --json` shows `tests/<capability>` as each capability's `testsPath`
- [x] 2.2 [code] Update `CLAUDE.md`'s layout table for the test folders; verify by reading it
- [x] 2.3 [code] Run `specworks run lint`; verify it passes
