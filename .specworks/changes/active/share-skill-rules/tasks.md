# Tasks: share-skill-rules

## 1. Includes with parameters

- [x] 1.1 Add the stub `fill_includes(text, skill, shared)` in `src/specworks/tools/skills.py` that ignores parameters and fills in includes as today, with the extended `INCLUDE_RE` (REQ-INTEG-007); verify `specworks run lint` passes and the existing tests pass
- [x] 1.2 [test] Tests for AC-INTEG-007.1 to AC-INTEG-007.7 calling `fill_includes` with a fake `shared` (a parameter filled in, a quoted value, an unfilled placeholder, an unused key, no parameters copied exactly), `specworks skills` with a failing packaged include writing nothing and exiting 1, and every packaged skill filling in with no `{{` or include line left, asserting the pinned error fragments, tagged `@ac`; verify they fail on the stub where the behaviour is new
- [ ] 1.3 [code] Implement `fill_includes` and use it in `read_skill` as design.md decides (the include line, the three checks, `ToolError`), tagged `@req REQ-INTEG-007`; verify `specworks run lint` passes and `uv run specworks skills` still changes no file under `.claude/skills/`

## 2. The shared rules

- [x] 2.1 [test] Wording tests in `tests/test_skills.py`: `specworks-design`, `specworks-test` and `specworks-code` contain `<!-- specworks:include back-from-review`, and `specworks-test` and `specworks-code` contain `<!-- specworks:include start-implement` (REQ-INTEG-007); verify they fail on the current skills
- [ ] 2.2 [code] Write `_shared/back-from-review.md` and `_shared/start-implement.md` and replace the passages in the three skills with includes as design.md decides (REQ-INTEG-007); verify `uv run specworks skills` changes no file under `.claude/skills/` (`git status --short .claude/skills` is empty)
