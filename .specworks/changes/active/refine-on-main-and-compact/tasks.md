# Tasks: refine-on-main-and-compact

## 1. Refine starts clear and from the base branch

- [x] 1.1 [test] In `tests/test_skills.py`, add tests for B1-B11 (design.md, Pinned wording), reading `raw_skill_file("specworks-refine/SKILL.md")` and every packaged skill for B11; verify they fail on the current skill
- [x] 1.2 [code] In `src/specworks/skills/specworks-refine/SKILL.md`, add the `## Before step 1` section between the stance and `## Steps` with B1-B9 verbatim; verify `uv run ruff check src tests` and that `grep -n "Before step 1" src/specworks/skills/specworks-refine/SKILL.md` finds the heading before `## Steps`

## 2. Docs and installed copies

- [x] 2.1 [code] In `docs/architecture.md`, add the decision D1 (design.md, Pinned wording) to Architectural decisions, naming `(refine-on-main-and-compact)`; verify by reading the section
- [x] 2.2 [code] Refresh the installed skills with `uv run specworks skills`; verify `.claude/skills/specworks-refine/SKILL.md` contains `## Before step 1` and matches the packaged text
