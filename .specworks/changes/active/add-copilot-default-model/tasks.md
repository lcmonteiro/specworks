# Tasks: add-copilot-default-model

## 1. The harness block in the project config

- [ ] 1.1 Add `HARNESS_KEYS`, `HarnessConfig`, `load_harness` and `Config.harness` in `src/specworks/core/config.py`, the module refusal hook in `src/specworks/core/workspace.py`, and `"harness.model"` in `SETTABLE_KEYS` (`src/specworks/core/config_file.py`) as stubs (REQ-PROJ-003, REQ-PROJ-035); verify `uv run mypy` passes
- [ ] 1.2 [test] Write failing tests in `tests/project/` for AC-PROJ-003.11, AC-PROJ-003.12, AC-PROJ-025.8, AC-PROJ-035.1, AC-PROJ-035.2 and AC-PROJ-035.3, tagged `@ac <AC-ID>`; verify they fail on the stubs, not on imports
- [ ] 1.3 [code] Load and check `harness:` (a mapping of `model`, a non-empty string; refused in a module with the pinned message) (REQ-PROJ-003) tagged `@req REQ-PROJ-003`; verify `specworks context` loads a config with `harness: {model: o3}` and refuses `harness: {model: ""}`
- [ ] 1.4 [code] Write and clear `harness.model` with `set_config_value`, keeping comments (REQ-PROJ-025, REQ-PROJ-035) tagged `@req REQ-PROJ-035`; verify by running `specworks config set harness.model o3` in a scratch project and reading its config

## 2. config set from a module

- [ ] 2.1 [test] Write a failing test in `tests/cli/test_config_set.py` for AC-CLI-013.8, tagged `@ac AC-CLI-013.8`; verify it fails because the module's config is written
- [ ] 2.2 [code] Route `harness.*` to the top level's config in `config set` and name it in the key's help (REQ-CLI-013) tagged `@req REQ-CLI-013`; verify `specworks config set --help` names `harness.model`, and `uv run ruff check src` passes

## 3. Copilot's default chat model

- [ ] 3.1 Add `CopilotSession.default_model() -> str | None` in `src/specworks/harness/copilot.py` and `MODEL_CONFIG_KEY` in `src/specworks/harness/model.py` as stubs (REQ-HARNESS-013, REQ-HARNESS-010); verify `uv run mypy` passes
- [ ] 3.2 [test] Write failing tests in `tests/harness/` for AC-HARNESS-013.1, AC-HARNESS-013.2 and AC-HARNESS-013.3 with a fake HTTP transport, tagged `@ac <AC-ID>`; verify they fail on the stub
- [ ] 3.3 [code] Implement `default_model()`: `GET <api base>/models` with the session token, the first `data` entry with `is_chat_default`, None on any failure (REQ-HARNESS-013) tagged `@req REQ-HARNESS-013`; verify `uv run mypy` and `uv run ruff check src` pass

## 4. The model order and its error

- [ ] 4.1 [test] Write failing tests in `tests/harness/test_model.py` for AC-HARNESS-010.2, AC-HARNESS-010.5 and AC-HARNESS-010.6, and in `tests/cli/test_harness.py` for AC-CLI-022.8, tagged `@ac <AC-ID>`, asserting the pinned missing-model message; verify they fail on today's order
- [ ] 4.2 [code] Take the model from `SPECWORKS_MODEL_MODEL`, else the top level's `harness.model`, else `default_model()` for a stored login, else raise the pinned missing-model error (REQ-HARNESS-010, REQ-HARNESS-013, REQ-CLI-022) tagged `@req REQ-HARNESS-010`; verify in a scratch project with a config `harness.model` and `SPECWORKS_MODEL_API_KEY` set that `specworks harness` gets past the model check

## Workflow follow-up

- After implement, check by hand with a live github.com and GHE login that `specworks harness` starts with no model named (design Open Questions).
