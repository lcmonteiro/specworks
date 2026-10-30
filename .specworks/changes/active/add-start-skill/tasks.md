# Tasks: add-start-skill

## 1. The start skill

- [x] 1.1 [test] Wording checks in `tests/test_skills.py` for `specworks-start`: it refuses a project with a config and hands a repository with code over to `/specworks-adopt`; it recommends tooling as options (uv for Python, CMake or Bazel for C++); it shows the tree and asks "Create this structure? (yes/no)" before writing; it runs `specworks init --tools`, `specworks module add` and `specworks capability add`, and puts a `.gitkeep` in each code folder; it writes no language files; it ends with `/specworks-refine`; and `specworks-start` joins the skills excluded from the shared change-picking rule; verify they fail before 1.2
- [ ] 1.2 [code] Write `src/specworks/skills/specworks-start/SKILL.md` as in the proposal and refresh the installed copies with `uv run specworks skills`; verify the 1.1 checks, `specworks run test` and `specworks run lint` pass

## 2. The README

- [ ] 2.1 [code] List `/specworks-start` in `README.md` for an empty repository, next to `/specworks-adopt`; verify the README names both and `specworks run test` passes
