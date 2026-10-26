# Tasks: colour-safe-cli-tests

## 1. Plain CLI output in tests

- [x] 1.1 [test] Add a guard test in `tests/test_cli.py`: with `GITHUB_ACTIONS=true` and `FORCE_COLOR=1` set (monkeypatch), `init --dir x` exits 2 and its output holds no `\x1b` and contains `No such option: --dir`; remove the ANSI strip from `test_init_has_no_dir_option`; verify the guard test fails before 1.2 when run with those variables set
- [ ] 1.2 [code] In `tests/conftest.py`, an autouse fixture sets `TERM=dumb` for every test; verify `GITHUB_ACTIONS=true FORCE_COLOR=1 uv run pytest` and `uv run pytest` both pass, and `specworks run lint` passes
