# Tasks: dedupe-copilot-skills

## 1. The tools in the config

- [ ] 1.1 Add the stubs in design.md: `TOOL_IDS` and `Config.tools` in `src/specworks/core/config.py`, `save_tools` in `src/specworks/core/config_file.py` (REQ-PROJ-003, REQ-PROJ-022); verify `specworks run lint` passes
- [ ] 1.2 [test] Tests for AC-PROJ-003.6 (a non-list, empty or unknown `tools` fails naming `tools` and the known IDs), AC-PROJ-003.7 (`tools` in a module's config is refused), AC-PROJ-022.1 (saved with comments kept, loads back), AC-PROJ-022.2 (an existing list replaced, one entry), tagged `@ac`; and a test that `TOOLS` in `tools/skills.py` has the keys of `TOOL_IDS` in order; verify they fail before 1.3
- [ ] 1.3 [code] Load and check `tools` (top level only) and implement `save_tools` as a text edit that reloads and restores on a bad result (REQ-PROJ-003, REQ-PROJ-022), tagged `@req`; verify the 1.2 tests pass

## 2. Installing for the chosen tools

- [ ] 2.1 Add the stubs in design.md in `src/specworks/tools/skills.py`: `Tool.reads`, `PROMPTS_DIR`, `skill_folders`, `resolve_tools`, `skills_state(root, saved)` (REQ-INTEG-004, REQ-INTEG-005, REQ-INTEG-006); verify `specworks run lint` passes
- [ ] 2.2 [test] Tests for AC-INTEG-004.5, AC-INTEG-004.6, AC-INTEG-004.7 (saved tools used, `--tools` saved, inferred tools saved), AC-INTEG-005.1, AC-INTEG-005.2, AC-INTEG-005.7 (updated: no prompt files, frontmatter per folder), AC-INTEG-005.8 (Claude Code + Copilot in `.claude/skills/` only), AC-INTEG-005.9 (old copies removed and printed, the user's own kept), AC-INTEG-006.3 (updated: a missing skill), AC-INTEG-006.6 (old copies `stale`), tagged `@ac`; remove the test of the retired AC-INTEG-005.3; verify the new ones fail before 2.3
- [ ] 2.3 [code] Implement `skill_folders`, `expected_skills` without prompt files, the wider stale search with `PROMPTS_DIR`, `resolve_tools` and `skills_state` with the saved tools; remove `prompts_dir` and `render_prompt` (REQ-INTEG-004, REQ-INTEG-005, REQ-INTEG-006), tagged `@req`; verify the 2.2 tests pass

## 3. init and update

- [ ] 3.1 Add the stubs in design.md: `is_terminal` in `src/specworks/cli/project.py`, `ToolsOpt` defaulting to `None` in `src/specworks/cli/output.py` (REQ-CLI-003, REQ-CLI-009); verify `specworks run lint` passes
- [ ] 3.2 [test] Tests for AC-CLI-003.9, AC-CLI-003.10, AC-CLI-003.11, AC-CLI-003.12 (the question in a terminal with `is_terminal` replaced, the default answer, no terminal, `--tools` or a saved choice), AC-CLI-009.3 (updated: the inferred tools saved), AC-CLI-009.5 (both tools, one folder, up to date), tagged `@ac`; verify they fail before 3.3
- [ ] 3.3 [code] `init`, `skills` and `update` resolve the tools with `resolve_tools`, `init` asks before writing anything when the design says so, and each saves the tools with `save_tools` when asked (REQ-CLI-003, REQ-CLI-009), tagged `@req`; verify the 3.2 tests pass

## 4. The adopt skill and this repository

- [ ] 4.1 [test] A wording check in `tests/test_skills.py`: `specworks-adopt` asks the user which AI tools the project uses and runs `specworks init --tools <list>` (REQ-CLI-003); verify it fails before 4.2
- [ ] 4.2 [code] Edit `src/specworks/skills/specworks-adopt/SKILL.md` as in the proposal; run `uv run specworks skills --tools claude,copilot` in this repository (saves `tools:`, removes the `.github/skills/` and `.github/prompts/` copies) and update CLAUDE.md's line on the installed copies (REQ-CLI-003); verify the 4.1 check, `specworks run test` and `specworks run lint` pass
