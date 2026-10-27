# Tasks: add-expected-outcomes

## 1. Template and instructions

- [x] 1.1 [test] Add wording checks to `tests/test_skills.py`: the refinement template has `## Outcomes` between `## Problem` and `## Context`; the refinement instruction in `schema.yaml` has an **Outcomes** bullet, asks to paraphrase or reference sources, and no longer says "Quote the user's words"; the proposal instruction says every outcome is covered by a requirement or listed under Out of Scope; verify they fail before 1.2
- [ ] 1.2 [code] Edit `src/specworks/templates/refinement.md` and the refinement and proposal instructions in `src/specworks/schema.yaml` as in the proposal; verify the 1.1 checks pass and `tests/test_cli.py::test_instructions_for_refinement` still passes

## 2. Skills

- [x] 2.1 [test] Add wording checks to `tests/test_skills.py`: `specworks-refine` step 3 agrees the outcomes before the options and offers alternatives with a recommendation; `specworks-specify` covers every outcome with a requirement or under Out of Scope; `specworks-baseline` notes each bug's correct behaviour (alternatives with a recommendation) and writes it as the fix refinement's Outcomes; verify they fail before 2.2
- [ ] 2.2 [code] Edit the refine, specify and baseline skills in `src/specworks/skills/` as in the proposal and refresh the installed copies with `uv run specworks skills`; verify the 2.1 checks pass and `specworks run test` and `specworks run lint` pass
