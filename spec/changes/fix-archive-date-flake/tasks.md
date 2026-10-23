# Tasks: fix-archive-date-flake

## 1. Pin the date

- [x] 1.1 [test] In `tests/test_archive.py`, add an autouse fixture that pins `specworks.specs.merge.date` to a fixed `TODAY` and build `ARCHIVED` from it; verify `uv run pytest tests/test_archive.py` passes

## 2. Checks

- [x] 2.1 [test] Run `uv run pytest -q`, `uv run ruff check src tests` and `uv run mypy`; verify all pass
