# Tasks: add-config-set

## 1. Setting a value in the config

- [x] 1.1 Add the stubs in design.md's Interfaces: `SETTABLE_KEYS` and `set_config_value` in `src/specworks/core/config_file.py` (REQ-PROJ-025); verify `specworks run lint` passes
- [x] 1.2 [test] Tests for AC-PROJ-025.1 to AC-PROJ-025.9 on sample configs (the default from `init`, a config without `commands:`, a context block, `commands: {test: pytest}`), asserting the loaded config, the comments kept, one line per key, the file unchanged on refusal, and the error fragments pinned in design.md, tagged `@ac`; verify they fail on the stubs
- [x] 1.3 [code] Implement `SETTABLE_KEYS` and `set_config_value` as design.md decides (keys, writing a command, writing the context, the check after writing), tagged `@req REQ-PROJ-025`; verify `specworks run lint` passes and, on a scratch copy of the default config, setting `commands.test` and a three-line `context` leaves a file that `specworks context` loads with both and its comments kept

## 2. The command

- [x] 2.1 Add the stub `config_app` in `src/specworks/cli/app.py` and `config_set` in `src/specworks/cli/project.py` (REQ-CLI-013); verify `specworks config set --help` shows `--file` and `--module`
- [x] 2.2 [test] Tests for AC-CLI-013.1 (`--json` fields, the relative config path, `specworks context` showing the command), AC-CLI-013.2 (`--file` and `--file -` with standard input), AC-CLI-013.3 (both and neither refused, config unchanged), AC-CLI-013.4 (`--module billing`, the top level unchanged) and AC-CLI-013.5 (`{"error": ...}`, exit 1, config unchanged), tagged `@ac`; verify they fail on the stubs
- [x] 2.3 [code] Implement `config set` as design.md decides (value or file, standard input, `--module`, the output), tagged `@req REQ-CLI-013`; verify `specworks run lint` passes and, in a scratch project, `specworks config set commands.test "uv run pytest" --json` prints the key, value and `.specworks/config.yml`

## 3. The skills

- [x] 3.1 [test] Wording tests in `tests/test_skills.py` for the skill phrases pinned in design.md, and that none of the five files contains ``under `commands:` `` or ``under `context:` `` (REQ-CLI-013); verify they fail on the current skills
- [x] 3.2 [code] Rewrite the steps in `specworks-adopt`, `specworks-start`, `specworks-test`, `specworks-code` and `_shared/phase-subagents.md` with the pinned wording, then refresh the installed copies with `uv run specworks skills` (REQ-CLI-013); verify `grep -rn 'config set' .claude/skills` lists each phrase
