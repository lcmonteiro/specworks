# Tasks: project-docs

## 1. A module's docs folder and `context`

- [x] 1.1 Add the stubs in design.md's Interfaces to `src/specworks/core/workspace.py`: `ARCHITECTURE_FILE`, `Module.docs_path` and `Module.architecture_path` (returning `root` and `root / ARCHITECTURE_FILE` for now) (REQ-PROJ-029); verify `specworks run lint` passes and the existing tests pass
- [ ] 1.2 [test] Write failing tests for AC-PROJ-029.1 to AC-PROJ-029.3 (the top level's `docs` and `docs/architecture.md`, a module's own `docs_dir`, a capability on `.` sharing the folder and loading) and AC-CLI-004.6 (`context --json` modules with `docsPath` and `hasArchitecture`), tagged `@ac`; verify they fail for the right reason
- [ ] 1.3 [code] Implement `Module.docs_path`/`architecture_path` and add `docsPath` and `hasArchitecture` to `module_dict` (REQ-PROJ-029, REQ-CLI-004), tagged `@req`; verify `specworks run lint` passes and `specworks context --json` on this repo shows the `(top)` module with `docsPath` `docs` and `hasArchitecture` false

## 2. Close needs the architecture

- [ ] 2.1 [test] Write a `docs/architecture.md` in the sample projects the tests close (in `tests/helpers.py` or `tests/samples.py`), so existing close tests keep passing, and write failing tests for AC-CLI-007.4 (close refused naming `docs/architecture.md`, nothing written, no command run, change still active; `--dry-run` shows the plan and `missing`), tagged `@ac AC-CLI-007.4`; verify they fail for the right reason
- [ ] 2.2 [code] Refuse `close` without the module's architecture before validate, and report `missing` in the dry run, with the wording in design.md's Interfaces (REQ-CLI-007), tagged `@req REQ-CLI-007`; verify `specworks run lint` passes and `specworks close --change project-docs --dry-run --no-run` on this repo names `docs/architecture.md` as missing

## 3. Validate warns on the architecture diagram

- [x] 3.1 Add the stub `architecture_diagrams_current` (returning `None`) in `src/specworks/workflow/validate.py` and list it in `VALIDATE` under coherence (REQ-FLOW-013); verify `specworks run lint` passes and the existing tests pass
- [ ] 3.2 [test] Write failing tests for AC-FLOW-013.9 (a module's `docs/diagrams/architecture-blocks.d2` with no SVG, then an outdated one: a non-blocking warning naming the SVG, the verdict unchanged; up to date or no `docs/diagrams/`: no such check), tagged `@ac AC-FLOW-013.9`; verify they fail for the right reason
- [ ] 3.3 [code] Implement `architecture_diagrams_current` as design.md decides (REQ-FLOW-013), tagged `@req REQ-FLOW-013`; verify `specworks run lint` passes and `specworks validate --change project-docs --no-run --json` on this repo shows no architecture-diagram check (no `docs/diagrams/` yet)

## 4. The skills write and read the architecture

- [ ] 4.1 [test] Add wording checks to `tests/test_skills.py` for the pinned wording in design.md: each line of `_shared/architecture.md` and `_shared/reading-architecture.md`, the `architecture` include in close, adopt and start, and the `reading-architecture` include in refine, specify, design, review and onboard (REQ-PROJ-029); verify they fail before 4.2
- [ ] 4.2 [code] Write `src/specworks/skills/_shared/architecture.md` and `_shared/reading-architecture.md` with the pinned wording, include them in the skills named in design.md (close: its living-docs step, before `specworks close`; adopt and start: once the capabilities are mapped; the others: at their first step), then refresh the installed copies with `uv run specworks skills` (REQ-PROJ-029); verify `specworks context` reports the skills current and `specworks run lint` passes
