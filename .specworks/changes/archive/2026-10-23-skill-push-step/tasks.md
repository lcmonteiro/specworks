# Tasks: skill-push-step

## 1. Placement of the pushing block

- [x] 1.1 [code] In `src/specworks/skills/specworks-done/SKILL.md` and `src/specworks/skills/specworks-close/SKILL.md`, put the `pushing` include on its own with a blank line before it, and unindent the next-steps text after it; verify by reading both skills
- [x] 1.2 [code] Refresh the installed copies with `specworks skills`; verify `git diff` shows only the close and done skill files and prompts changed

## 2. Checks

- [x] 2.1 [test] Run `uv run pytest tests/test_skills.py` and `uv run ruff check src tests`; verify both pass
