# Tasks: add-langfuse-monitoring

## 1. The telemetry config

- [x] 1.1 Add `TelemetryConfig`, `TELEMETRY_KEYS`, `load_telemetry` and `Config.telemetry` in `src/specworks/core/config.py`, and `telemetry.langfuse` / `telemetry.host` in `SETTABLE_KEYS`, as stubs (REQ-PROJ-003, REQ-PROJ-032); verify `uv run mypy` passes and existing tests pass
- [ ] 1.2 [test] Write failing tests in `tests/project/` for AC-PROJ-003.9, AC-PROJ-003.10, AC-PROJ-025.8, AC-PROJ-032.1, AC-PROJ-032.2, AC-PROJ-032.3 tagged `@ac`; verify they fail on the missing behaviour, not on imports
- [ ] 1.3 [test] Write a failing test in `tests/cli/` for AC-CLI-013.7 tagged `@ac AC-CLI-013.7`; verify it fails on the missing behaviour
- [ ] 1.4 [code] Load and check the `telemetry` block, refuse it in a module's config (`core/workspace.py`) (REQ-PROJ-003) tagged `@req REQ-PROJ-003`; verify `uv run specworks context` still loads this repo and a config with `telemetry: {langfuse: maybe}` is refused naming `telemetry.langfuse`
- [ ] 1.5 [code] Set `telemetry.langfuse` and `telemetry.host` as one line each under `telemetry:` (generalising `_set_command`), refusing bad values before writing (REQ-PROJ-025, REQ-PROJ-032) tagged `@req REQ-PROJ-032`; verify by running `config set telemetry.langfuse true` on a scratch project and reading its config
- [ ] 1.6 [code] Make `config set telemetry.*` always write the top level's config (REQ-CLI-013) tagged `@req REQ-CLI-013`; verify from a scratch module that the top level's config changes and the module's does not

## 2. The event log and the trace identity

- [x] 2.1 Add `src/specworks/core/events.py` with `record_event`, `read_unsent`, `mark_sent`, `trace_id`, `session_id` and the file constants as stubs (REQ-PROJ-030, REQ-PROJ-031); verify `uv run mypy` passes
- [ ] 2.2 [test] Write failing tests in `tests/project/` for AC-PROJ-030.1, AC-PROJ-030.2, AC-PROJ-030.3, AC-PROJ-030.4, AC-PROJ-030.5, AC-PROJ-031.1, AC-PROJ-031.2 tagged `@ac`; verify they fail on the missing behaviour
- [ ] 2.3 [code] Append events as UTC-stamped JSON lines, write the change folder's `.gitignore`, write nothing when off, swallow write errors (REQ-PROJ-030) tagged `@req REQ-PROJ-030`; verify `uv run ruff check src && uv run mypy`, and on a scratch change that `git status` does not list `events.jsonl`
- [ ] 2.4 [code] Derive the trace ID from the module label, name and creation time, and the session ID from the ref (REQ-PROJ-031) tagged `@req REQ-PROJ-031`; verify `uv run mypy` and that two calls give the same 32 hex characters
- [ ] 2.5 [code] Read the unsent lines after `events.sent` (skipping lines that are not JSON objects, still counted) and add to the count (REQ-INTEG-009 support in `core/events.py`) tagged `@req REQ-INTEG-009`; verify `uv run mypy`

## 3. The Langfuse client

- [x] 3.1 Add `src/specworks/tools/langfuse.py` with `LangfuseSettings`, `langfuse_settings`, `SendResult`, `send_events` and the constants as stubs (REQ-INTEG-008, REQ-INTEG-009); verify `uv run mypy` passes
- [ ] 3.2 [test] Write failing tests in `tests/integrations/` for AC-INTEG-008.1, AC-INTEG-008.2, AC-INTEG-008.3, AC-INTEG-008.4, AC-INTEG-008.5 tagged `@ac`; verify they fail on the missing behaviour
- [ ] 3.3 [test] Write failing tests in `tests/integrations/` for AC-INTEG-009.1, AC-INTEG-009.2, AC-INTEG-009.3, AC-INTEG-009.4, AC-INTEG-009.5, AC-INTEG-009.6 against a local `http.server` on a free port (accepting, answering 500/401, or never answering) tagged `@ac`; verify they fail on the missing behaviour and the no-answer test finishes within 10 s
- [ ] 3.4 [code] Compute the state, host and keys from the config and `SPECWORKS_LANGFUSE_*` only, keys left out of `repr` (REQ-INTEG-008) tagged `@req REQ-INTEG-008`; verify `uv run mypy` and that `repr(settings)` holds no key
- [ ] 3.5 [code] Build the ingestion batches (trace-create, then span-create per line with stable IDs), POST them with basic auth and a 5 s timeout via `urllib.request`, stop at the first failure with a key-free reason, mark sent per accepted batch (REQ-INTEG-009) tagged `@req REQ-INTEG-009`; verify `uv run ruff check src && uv run mypy`, and against a scratch Langfuse or local server that a batch arrives

## 4. Recording events in the commands

- [x] 4.1 Add `src/specworks/cli/telemetry.py` with `record` as a stub (REQ-CLI-017); verify `uv run mypy` passes
- [ ] 4.2 [test] Write failing tests in `tests/cli/` for AC-CLI-017.1, AC-CLI-017.2, AC-CLI-017.3, AC-CLI-017.4, AC-CLI-017.5 tagged `@ac`; verify they fail on the missing behaviour
- [ ] 4.3 [code] Implement `record` (opt-in from the top level's config, `ms` from the start time) and call it from `new`, `phase`, `abandon`, `commit`, `start`, `gate`, `run --change`, `finding add|decide|done|close`, `cycle`, `validate` and `close` with only their listed fields, before emitting or exiting (REQ-CLI-017) tagged `@req REQ-CLI-017`; verify `uv run ruff check src && uv run mypy`, and on a scratch project with telemetry on that a failed `gate` adds a `gate` line

## 5. Sending at commit, and telemetry push

- [x] 5.1 Add `send_after_commit` and `telemetry_app` with `push` as stubs, registered as `specworks telemetry` in `src/specworks/cli/app.py` (REQ-CLI-012, REQ-CLI-018); verify `uv run specworks telemetry push --help` runs
- [ ] 5.2 [test] Write failing tests in `tests/cli/` for AC-CLI-012.5, AC-CLI-012.6, AC-CLI-012.7, AC-CLI-018.1, AC-CLI-018.2, AC-CLI-018.3 tagged `@ac`; verify they fail on the missing behaviour
- [ ] 5.3 [code] After committing, record the `commit` event, send when the state is `on`, print the sent count or the reason, queued count and `specworks telemetry push` hint, add `telemetry` to `--json`, keep the exit code (REQ-CLI-012) tagged `@req REQ-CLI-012`; verify `uv run mypy`, and on a scratch project with an unreachable host that `commit` exits 0 and says the events are queued
- [ ] 5.4 [code] Implement `telemetry push`: active or newest archived change, refuse `off` / `keys missing` naming the reason, print `sent`/`queued`/`reason`, exit 1 when events remain (REQ-CLI-018) tagged `@req REQ-CLI-018`; verify `uv run mypy`, and without keys that it fails naming `SPECWORKS_LANGFUSE_PUBLIC_KEY`

## 6. Telemetry in context and status

- [x] 6.1 Add `telemetry_state` and `telemetry_ids` as stubs in `src/specworks/cli/telemetry.py` (REQ-CLI-004, REQ-CLI-019); verify `uv run mypy` passes
- [ ] 6.2 [test] Write failing tests in `tests/cli/` for AC-CLI-004.7 and AC-CLI-019.1 tagged `@ac`; verify they fail on the missing behaviour
- [ ] 6.3 [code] Add `telemetry` (`state`, `host`, never a key) to `context` (REQ-CLI-004) tagged `@req REQ-CLI-004`; verify `uv run specworks context --json` shows `telemetry.state` `off` in this repo
- [ ] 6.4 [code] Add `telemetry` (`traceId`, `sessionId`) to `status --json` for active and archived changes (REQ-CLI-019) tagged `@req REQ-CLI-019`; verify `uv run specworks status --change add-langfuse-monitoring --json` shows both

## Workflow follow-up

- Document the setup (opt-in, `SPECWORKS_LANGFUSE_*`) in the GitHub wiki.
- Follow-up change: pass the trace and session IDs to Claude Code's OTel export once checked against Langfuse.
