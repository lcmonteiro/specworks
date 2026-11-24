# Tasks: refine-says-when-not-worth-it

## 1. Refine says when a request is not a good idea

- [x] 1.1 [test] In `tests/test_skills.py`, add wording tests for the pinned phrases of design.md: the **Candid** stance bullet, the step 3 stop (`"I don't think this is a good idea: <why>"`, `Never abandon on your own`, the `specworks abandon --change "<ref>" --reason "<why>"` option), the step 5 abandon option, and `Not recommended: <why>` in the refinement instruction (`specworks instructions refinement`); verify they fail before 1.2 and 1.3
- [x] 1.2 [code] In `src/specworks/skills/specworks-refine/SKILL.md`, add the **Candid** stance bullet, the step 3 paragraph and the step 5 line, verbatim from design.md; verify by reading the skill: each phrase of design.md is there word for word
- [x] 1.3 [code] In `src/specworks/schema.yaml`, extend the refinement instruction's **Recommendation** bullet verbatim from design.md; verify with `uv run specworks instructions refinement --change "<ref>"`: the Recommendation bullet shows `Not recommended: <why>`
- [x] 1.4 [code] Refresh the installed copies with `uv run specworks skills`; verify `git status` shows `.claude/skills/specworks-refine/SKILL.md` changed to match the source
