# Tasks: architecture-docs

## 1. The design instruction and template

- [ ] 1.1 [test] Wording checks in `tests/test_skills.py`: the design instruction in `schema.yaml` names a change to components or their dependencies as a reason to write `design.md`, asks for a block diagram for such a change and "No structural change" otherwise; the design template's `## Diagrams` comment says the same; verify they fail before 1.2
- [x] 1.2 [code] Edit the design instruction in `src/specworks/schema.yaml` and `src/specworks/templates/design.md` as in the proposal; verify the 1.1 checks pass and `specworks run test` passes

## 2. The skills and comments

- [ ] 2.1 [test] Wording checks in `tests/test_skills.py`: no packaged skill mentions `architecture.md`; `specworks-close` step 4 keeps one block diagram of the capability in the living `design.md`; `specworks-baseline` draws a block diagram for a capability with more than one component; `specworks-specify` step 6 follows the structural-change rule; and the default config written by `init` does not mention `architecture.md`; verify they fail before 2.2
- [x] 2.2 [code] Edit the specify, close, baseline and refine skills in `src/specworks/skills/`, the comments in `src/specworks/core/config.py` and `src/specworks/core/config_file.py`, and this repository's `.specworks/config.yml`, as in the proposal; refresh the installed copies with `uv run specworks skills`; verify the 2.1 checks, `specworks run test` and `specworks run lint` pass
