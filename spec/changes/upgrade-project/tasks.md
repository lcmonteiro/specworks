# Tasks: upgrade-project

## 1. Skills state

- [x] 1.1 Add `expected_skills`, `installed_tools`, `SkillFile`, `SkillsState`, `skills_state` and `update_skills` to `src/specworks/tools/skills.py` as stubs (REQ-INTEG-006, REQ-CLI-009); verify it builds and existing tests pass
- [ ] 1.2 Write failing tests in `tests/test_skills.py` for AC-INTEG-006.1, AC-INTEG-006.2, AC-INTEG-006.3, AC-INTEG-006.4, AC-INTEG-006.5 tagged `@ac`; verify they fail on the stubs
- [ ] 1.3 Implement `expected_skills` (and rebuild `install_skills` on it), `installed_tools` and `skills_state` (REQ-INTEG-006) tagged `@req REQ-INTEG-006`; verify the 1.2 tests and the existing AC-INTEG-005.x tests pass

## 2. update command

- [x] 2.1 Add the `specworks update` command to `src/specworks/cli/project.py` as a stub (REQ-CLI-009); verify `specworks update --help` runs
- [ ] 2.2 Write failing tests in `tests/test_cli.py` for AC-CLI-009.1, AC-CLI-009.2, AC-CLI-009.3, AC-CLI-009.4 tagged `@ac`; verify they fail on the stub
- [ ] 2.3 Implement `update_skills` and the `update` command (REQ-CLI-009) tagged `@req REQ-CLI-009`; verify the 2.2 tests pass

## 3. Skills state in context

- [ ] 3.1 Write failing tests for AC-CLI-004.5 (JSON `skills` and the text hint) tagged `@ac`; verify they fail
- [ ] 3.2 Show the skills state in `context` (REQ-CLI-004) tagged `@req REQ-CLI-004`; verify the 3.1 tests and AC-CLI-004.1-4 pass

## 4. Docs and checks

- [ ] 4.1 Add an "Upgrade" part to the README's Install section: `uv tool upgrade specworks`, then `specworks update` (REQ-CLI-009); verify by reading it
- [ ] 4.2 Run `specworks run test` and `specworks run lint` (95% branch coverage included); verify both pass
