# Refinement: add-copilot-login

## Problem

`specworks harness` needs a model key in `SPECWORKS_MODEL_API_KEY`, a model in `SPECWORKS_MODEL_MODEL` and, for a non-OpenAI endpoint, `SPECWORKS_MODEL_BASE_URL`. A user with a GitHub Copilot plan has no such key: reaching Copilot's OpenAI-compatible API takes a GitHub device-flow login and an exchange for a short-lived session token. The user wants one command, `specworks login copilot`, so the harness runs on their Copilot plan without setting those variables by hand. The login logic already exists, written for another project (`copilot_auth.py`, from the user's `space-ai` repository).

## Outcomes

- `specworks login copilot` shows a GitHub verification URL and code, waits for the user to authorise, and reports success without printing any token.
- After it, `specworks harness` starts and talks to Copilot with only `SPECWORKS_MODEL_MODEL` set: no key, no base URL, no `export`.
- The harness keeps working past the ~25 minute life of a Copilot session token (no re-login mid-chat).
- An explicit `SPECWORKS_MODEL_API_KEY` still wins: a user with their own key sees no change.
- Without a stored login and without a key, the harness fails as today, naming `SPECWORKS_MODEL_API_KEY`, and the message mentions `specworks login copilot`.
- No token, OAuth or session, appears in any output, error, log, `chat.jsonl` or peer shell.

## Context

**Observed:**
- `src/specworks/harness/model.py`: `model_from_env` builds `ChatOpenAI` from `SPECWORKS_MODEL_API_KEY` (required), `SPECWORKS_MODEL_MODEL` (required) and optional `SPECWORKS_MODEL_BASE_URL`; the key is a `SecretStr`. Called once by `run_harness` before the session opens.
- `harness` capability, REQ-HARNESS-010: a key's value never appears in any output, error, file or message; `confine.shell_env` hides `SPECWORKS_MODEL_*` from peer shells.
- `src/specworks/cli/harness.py`: `harness` imports the harness lazily and tells the user which extra to install; no `login` command exists. The CLI is a flat typer `app` with `--json` and errors as values (`cli` capability).
- `copilot_auth.py` (external): GitHub OAuth device flow with the public GitHub CLI client id; caches the OAuth token in `~/.config/copilot_model/token.json` (dir 0700, file 0600); exchanges it at `copilot_internal/v2/token` for a session token (≈25 min) and the API base (`endpoints.api`); `CopilotTokenProvider` refreshes on expiry; supports a GitHub Enterprise host. It uses `httpx`, `asyncio`, `print` and `logging` (and opens a browser).
- `httpx` is not a base dependency of specworks; it comes with the `harness` extra (via `langchain-openai`).

**Assumed:**
- A fresh session token can be handed to `ChatOpenAI` per request (a callable or async `api_key`, or a custom client auth) so it refreshes while the chat runs; to confirm against the pinned `langchain-openai` in the design phase.
- The editor headers (`Editor-Version`, …) the exchange sends are still what Copilot's API requires, and the model's own requests may need them too.
- The token exchange is an unofficial endpoint and may change.

## Constraints

- [hard] A command cannot set its parent shell's environment: the login must persist its result in a file, not in variables.
- [hard] REQ-HARNESS-010: a token's value never appears in output, errors, logs or `chat.jsonl`. Only the long-lived OAuth token may be stored, owner-only (dir 0700, file 0600); a session token is never stored.
- [hard] An explicit `SPECWORKS_MODEL_API_KEY` takes precedence; `SPECWORKS_MODEL_MODEL` stays required (decided: the user names the model).
- [hard] No other command loads the extra: `login` imports its code lazily and, if the extra is missing, says which to install (as `harness` does).
- [hard] CLI conventions: `--json`, errors as `{"error": ...}` with exit 1; 95% branch coverage, so network calls are testable with a fake transport.
- [soft] The stored login lives in a specworks-owned path, not in `~/.config/copilot_model/` of the other project.
- [soft] Support `--ghe-host` for GitHub Enterprise, as the source does.

## Options

### Option A: Stored login, harness exchanges and refreshes (chosen)

`login copilot` runs the device flow and stores only the OAuth token (and the GHE host) in a user-level specworks file. When `SPECWORKS_MODEL_API_KEY` is unset and a login exists, `model_from_env` builds `ChatOpenAI` with the Copilot API base and a key that is a fresh session token each time it is needed (exchanged from the stored OAuth token, refreshed near expiry).

- **Pros:** nothing to export; no session token printed or stored; survives token expiry; fits REQ-HARNESS-010.
- **Cons:** the harness gains a second way to get a model, and a per-request token needs the client built for it; depends on an unofficial endpoint.
- **Effort:** M
- **Touches:** `harness` (model from login, the Copilot token provider), `cli` (the `login` command).
- **Outcomes:** meets all; fails none.

### Option B: Print `export` lines

`eval "$(specworks login copilot)"` prints `SPECWORKS_MODEL_API_KEY=<session token>` and `SPECWORKS_MODEL_BASE_URL`.

- **Pros:** literally sets the environment; the harness is unchanged; S effort.
- **Cons:** the token is printed (breaks the never-in-output rule); it expires in ~25 min, so every long chat dies; must be re-run each time.
- **Effort:** S
- **Touches:** `cli`.
- **Outcomes:** meets the first outcome only partly; fails "keeps working past 25 minutes" and "no token in any output".

### Option C: Both A and the `--env` export

Option A, plus `login copilot --env` for the exports of B.

- **Pros:** covers other tools that read the variables.
- **Cons:** still prints a short-lived token; more surface for a need nobody has stated.
- **Effort:** M
- **Touches:** `harness`, `cli`.
- **Outcomes:** meets all except "no token in any output" when `--env` is used.

## Recommendation

Option A, agreed with the user. Scope: `specworks login copilot` (device flow, stored OAuth token, `--ghe-host`), code in `harness` and needing the `harness` extra, used only when `SPECWORKS_MODEL_API_KEY` is unset. Out: `logout`, other providers, exporting variables, a stored default model.

## Open Questions

- Does the pinned `langchain-openai` accept a refreshable key (callable/async) on `ChatOpenAI`, or does the harness need a small custom auth on the client? (who can answer: the design phase, by reading the library)
- Where should the stored login live: `~/.config/specworks/` (honouring `XDG_CONFIG_HOME`, and `%APPDATA%` on Windows, since CI runs on Windows and macOS)? (who can answer: the user, or decided in design)

## Candidate Capabilities

- `harness`: modified - `model_from_env` falls back to the stored Copilot login; new Copilot auth (device flow, token store, session-token provider).
- `cli`: modified - new `login copilot` command with `--json` and `--ghe-host`, and the harness error that points to it.
