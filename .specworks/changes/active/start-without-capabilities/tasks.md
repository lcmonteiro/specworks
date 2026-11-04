# Tasks: start-without-capabilities

## 1. Start creates the minimal tree

- [x] 1.1 [test] In `tests/test_skills.py`, replace `START_CREATE_WORDING`, `test_the_start_skill_no_longer_writes_the_gitkeep_by_hand` and the `capability add` asserts in the start tests with tests for S1-S6 (design.md, Pinned wording); verify they fail on the current skill
- [ ] 1.2 [code] Rewrite `src/specworks/skills/specworks-start/SKILL.md` (description, intro, boundary, steps 4-6, guardrails) for the minimal tree with S1-S6 verbatim; verify `uv run ruff check src tests` and grep for `capability add` in the skill returns nothing

## 2. Onboard routes a started project to refine

- [x] 2.1 [test] In `tests/test_skills.py`, add tests for O1-O4 (design.md, Pinned wording); verify they fail on the current skill
- [ ] 2.2 [code] Replace the `capabilities` is empty row of `src/specworks/skills/specworks-onboard/SKILL.md` with rows O1 and O2 (O3 in O2's next step); verify the table renders with the same columns

## 3. Refinement proposes the capabilities

- [x] 3.1 [test] In `tests/test_skills.py`, add tests for R1 (the refinement instruction from `load_artifacts()`), R2 (`read_template("refinement.md")`) and F1 (the refine skill); verify they fail on the current text
- [ ] 3.2 [code] Update the refinement instruction in `src/specworks/schema.yaml`, `src/specworks/templates/refinement.md` and the refine skill's guardrail with R1, R2 and F1 verbatim; verify `uv run specworks instructions refinement --change start-without-capabilities --json` shows them

## 4. README and installed copies

- [ ] 4.1 [code] Describe `/specworks-start` in `README.md` without capabilities (minimal tree; capabilities proposed in each change's refinement); verify by reading the section
- [ ] 4.2 [code] Refresh the installed skills with `uv run specworks skills`; verify `.claude/skills/specworks-start/SKILL.md` matches the packaged text
