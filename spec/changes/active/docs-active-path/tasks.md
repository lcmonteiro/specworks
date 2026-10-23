# Tasks: docs-active-path

## 1. Text

- [x] 1.1 [code] Change `spec/changes/` to `spec/changes/active/` in `CLAUDE.md` and in the `init` line of `README.md`; verify with `grep -n "spec/changes" CLAUDE.md README.md`

## 2. Checks

- [x] 2.1 [test] Run `uv run pytest -q`; verify it passes
