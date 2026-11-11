# Tasks: add-copilot-login

## 1. The stored login and the Copilot flow

- [x] 1.1 Add `Login`, `LoginStore`, `config_dir` (`logins.py`) and `CopilotLoginError`, `CopilotSession`, `device_login`, `LoginResult`, `log_in` (`copilot.py`) as stubs (REQ-HARNESS-011, REQ-HARNESS-012); verify `uv run mypy` passes
- [ ] 1.2 [test] Write failing tests in `tests/harness/test_copilot_login.py` on a fake `httpx` transport with injected sleep and clock, and a temporary config dir, for the login's storage and flow (AC-HARNESS-011.1, AC-HARNESS-011.2, AC-HARNESS-011.3, AC-HARNESS-011.4, AC-HARNESS-011.5, AC-HARNESS-011.6, AC-HARNESS-011.7, AC-HARNESS-011.8), tagged `@ac`; verify they fail for the right reason
- [ ] 1.3 [test] Write failing tests in `tests/harness/test_copilot_session.py` for the session token's renewal and the revoked login (AC-HARNESS-012.4, AC-HARNESS-012.5), tagged `@ac`; verify they fail for the right reason
- [ ] 1.4 [code] Implement `LoginStore` and `config_dir` in `logins.py`: global and per-project files in the user's config dir, owner-only, written by rename, token hidden from `repr` (REQ-HARNESS-011), tagged `@req REQ-HARNESS-011`; verify `uv run ruff check src` and `uv run mypy`
- [ ] 1.5 [code] Implement `device_login`, `CopilotSession` and `log_in` in `copilot.py`: the device flow with `slow_down`, denial and expiry, the exchange for a session token renewed 60 seconds before it expires, reuse of a working login, `--force`, a stale login, GitHub Enterprise hosts, and errors that carry no token (REQ-HARNESS-011, REQ-HARNESS-012), tagged `@req REQ-HARNESS-011` and `@req REQ-HARNESS-012`; verify `uv run ruff check src` and `uv run mypy`

## 2. The model from a stored login

- [x] 2.1 Extend `model_from_env` with the `root`, `store` and `client` keywords and make `run_harness` pass `root=ws.root`, as stubs that keep today's behaviour (REQ-HARNESS-010, REQ-HARNESS-012); verify `uv run mypy` passes
- [ ] 2.2 [test] Update `tests/harness/test_model.py`: the missing-key case with no login says to run `specworks login copilot` (AC-HARNESS-010.2), and the login's tokens never reach a reply, error, log line or `chat.jsonl` (AC-HARNESS-010.4); tagged `@ac`; verify they fail for the right reason
- [ ] 2.3 [test] Write failing tests in `tests/harness/test_model.py` for the key from a login, local before global, an explicit key that wins with no read and no exchange, and a user-set base URL (AC-HARNESS-012.1, AC-HARNESS-012.2, AC-HARNESS-012.3, AC-HARNESS-012.6), tagged `@ac`; verify they fail for the right reason
- [ ] 2.4 [code] Implement the stored-login branch of `model_from_env`: used only when the key is missing or empty, local login first, the first exchange at build time for the API base and an early failure, the session token as a callable key, the Copilot API base unless `SPECWORKS_MODEL_BASE_URL` is set, and the key error that points to `specworks login copilot` (REQ-HARNESS-010, REQ-HARNESS-012), tagged `@req REQ-HARNESS-010` and `@req REQ-HARNESS-012`; verify `uv run ruff check src` and `uv run mypy`

## 3. The login command

- [x] 3.1 Add the `login` command in `src/specworks/cli/login.py` (registered in `cli/__init__.py`) as a stub (REQ-CLI-023); verify `uv run specworks login --help` lists `--local`, `--global`, `--force`, `--ghe-host` and `--json`
- [ ] 3.2 [test] Write failing tests in `tests/cli/test_login.py` for the command: the default global scope, local, reuse, force, the prompt on stderr with clean JSON on stdout, both scopes, local with no project, another provider, a failed flow, no extra, and light imports (AC-CLI-023.1, AC-CLI-023.2, AC-CLI-023.3, AC-CLI-023.4, AC-CLI-023.5, AC-CLI-023.6, AC-CLI-023.7, AC-CLI-023.8, AC-CLI-023.9, AC-CLI-023.10, AC-CLI-023.11), tagged `@ac`; verify they fail for the right reason
- [ ] 3.3 [test] Update `tests/cli/test_harness.py`: no key and no login fails naming `SPECWORKS_MODEL_API_KEY` and `specworks login copilot` (AC-CLI-022.2), tagged `@ac`; verify it fails for the right reason
- [ ] 3.4 [code] Implement `login`: the provider argument, the scope flags and their conflict, `workspace()` for `--local`, the lazy import of the harness with the install message, the prompt to stderr, the JSON or one-line result, and errors as values (REQ-CLI-023, REQ-CLI-022), tagged `@req REQ-CLI-023` and `@req REQ-CLI-022`; verify `uv run ruff check src` and `uv run mypy`, and `uv run specworks login --help`

## Workflow follow-up

- `specworks skills` needs no refresh: no skill text changes.
- The README stays as it is; the user documentation lives in the wiki.
