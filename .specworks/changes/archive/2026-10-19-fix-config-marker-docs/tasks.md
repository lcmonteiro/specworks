# Tasks: fix-config-marker-docs

## 1. Docstring

- [x] 1.1 Reword the `src/specworks/core/config.py` module docstring: an unindented `specworks: <n>` line, anywhere in the file, marks a specworks config; verify `git diff` touches only the docstring and `uv run pytest` and lint pass
