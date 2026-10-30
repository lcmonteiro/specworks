# Tasks: add-start-skill

## 1. The start skill

- [x] 1.1 [test] Wording checks in `tests/test_skills.py` for `specworks-start`: it refuses a project with a config and hands a repository with code over to `/specworks-adopt`; it recommends tooling as options (uv for Python, CMake or Bazel for C++); it shows the tree and asks "Create this structure? (yes/no)" before writing; it runs `specworks init --tools`, `specworks module add` and `specworks capability add`, and puts a `.gitkeep` in each code folder; it writes no language files; it ends with `/specworks-refine`; and `specworks-start` joins the skills excluded from the shared change-picking rule; verify they fail before 1.2
- [x] 1.2 [code] Write `src/specworks/skills/specworks-start/SKILL.md` as in the proposal and refresh the installed copies with `uv run specworks skills`; verify the 1.1 checks, `specworks run test` and `specworks run lint` pass
- [x] 1.3 [test] In `tests/test_skills.py`, make `test_start_ends_by_handing_over_to_refine` accept the closing options as every skill writes them in a code block (`1. /specworks-refine <first change> (recommended)`, no backticks); verify it passes against the skill
- [ ] 1.4 [test] Review R1 and R2 in `tests/test_skills.py`: `test_start_refuses_a_set_up_project_and_hands_existing_code_to_adopt` checks that start goes on with the fresh config `init` wrote and says to run `specworks init` when there is none; `test_start_shows_the_tree_and_asks_before_writing` and `test_start_creates_the_structure_with_the_cli_and_a_gitkeep_per_code_folder` expect `specworks skills --tools <list>` after "Create this structure? (yes/no)" and no `specworks init` in the creating step; `test_start_recommends_the_tooling_as_options` checks `(recommended)`, uv with Python, and CMake, Bazel and C++ in the tooling step's text alone; verify the R1 checks fail before 1.5
- [ ] 1.5 [code] Review R1: rewrite steps 1 and 5 of `src/specworks/skills/specworks-start/SKILL.md` (start runs after `init` and goes on with its fresh config; step 5 runs `specworks skills --tools <list>` instead of `init`), and the Boundary and Guardrails lines that name `init`; refresh the installed copies with `uv run specworks skills`; verify the 1.4 checks, `specworks run test` and `specworks run lint` pass

## 2. The README

- [x] 2.1 [code] List `/specworks-start` in `README.md` for an empty repository, next to `/specworks-adopt`; verify the README names both and `specworks run test` passes
- [ ] 2.2 [code] Review R1: the README keeps `specworks init` and then lists `/specworks-start` for a repository with no code yet (not "it runs `init` for you"); verify the README no longer says start runs `init`
