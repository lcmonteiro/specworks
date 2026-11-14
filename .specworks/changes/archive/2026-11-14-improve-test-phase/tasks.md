# Tasks: improve-test-phase

## 1. Test rules and specify scenarios

- [x] 1.1 [test] In `tests/test_skills.py`, add wording tests for the pinned phrases of design.md: `Rank the criteria by risk first`, `write no untagged test: name it in the report as a missing scenario` and `would it fail if the THEN broke?` in `specworks-test`, and `at least one error or limit scenario` in `specworks-specify`; verify they fail before 1.2 and 1.3
- [x] 1.2 [code] In `src/specworks/skills/specworks-test/SKILL.md`, step 4: open with the risk rule, add the negative-cases bullet, extend "Pick the level" with the integration rule, replace "Keep tests deterministic" with the quality rule; step 7: list the missing scenarios in the report; all verbatim from design.md; verify by reading the step and `uv run specworks skills`
- [x] 1.3 [code] In `src/specworks/skills/specworks-specify/SKILL.md`, step 4: add the error or limit scenario rule verbatim from design.md; verify by reading the step
- [x] 1.4 [code] Refresh the installed copies with `uv run specworks skills`; verify `git status` shows `.claude/skills/specworks-test/SKILL.md` and `.claude/skills/specworks-specify/SKILL.md` changed to match the sources
