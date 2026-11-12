# Refinement: add-copilot-default-model

## Problem

`specworks login copilot` stores a working Copilot login, but `specworks
harness` still stops with `SPECWORKS_MODEL_MODEL is not set`. The stored
login can stand in for the API key, but not for the model name, so a user who
has just logged in still has to find a valid Copilot model id and export it
by hand. This happens on GitHub.com and on GitHub Enterprise hosts alike.

## Outcomes

- After `specworks login copilot` (with or without `--ghe-host`), running
  `specworks harness` starts with no `SPECWORKS_MODEL_*` variable set.
- The harness reads its settings from the environment first, then from the
  files on disk: `SPECWORKS_MODEL_MODEL`, when set, still picks the model.
- `specworks login copilot --model <id>` lets the user pick a model other
  than Copilot's default.
- A stored login that has no model yet (made before this change) gives an
  error saying to run `specworks login copilot` again, before the session
  starts.

## Context

**Observed:**
- `harness` capability (`src/specworks/harness`, docs in
  `src/specworks/harness/docs`): REQ-HARNESS-010 always requires
  `SPECWORKS_MODEL_MODEL`. REQ-HARNESS-012 lets a stored login replace only
  `SPECWORKS_MODEL_API_KEY` and the base URL.
- `model.py` `model_from_env` raises `ModelSettingsError(MODEL_NAME)` when the
  name is missing, even after it has found a stored login.
- `logins.py` `Login` holds only `oauth_token` and `ghe_host`. `LoginStore`
  writes one global file and one file per project, in the user's config
  folder.
- `copilot.py` `CopilotSession` exchanges the OAuth token for a session token
  and takes the API base from the exchange's `endpoints.api`. `log_in` reuses
  a login that still exchanges, unless `--force` is given.
- `cli` capability: `cli/login.py` (REQ-CLI-023) has the `--local`,
  `--global`, `--force`, `--ghe-host` and `--json` options, but no model
  option.

**Assumed:**
- `GET <api base>/models` with the session token lists the models the login
  may use, and marks Copilot's default chat model (`is_chat_default`). Not yet
  checked against a live login.

## Constraints

- [hard] An explicit `SPECWORKS_MODEL_API_KEY` still ignores the stored logins,
  and still needs `SPECWORKS_MODEL_MODEL` (another provider has no default).
- [hard] Environment variables win over what is stored on disk.
- [hard] No token appears in any output, error or file other than the login
  file. The model id is not secret and may be shown.
- [hard] Login files written before this change, with no model, are still
  read without error by the store.
- [soft] The harness makes no extra request at startup to choose a model.

## Options

### Option A: login stores the model

At login, after the token exchange, ask Copilot's `/models` for its chat
default (or take `--model <id>`) and store it in the login file next to the
token. The harness takes the model from `SPECWORKS_MODEL_MODEL`, else from the
stored login.

- **Pros:** the harness reads only env and disk, with no extra request; the
  stored model is one the login could use at login time; the user can pin a
  model with `--model`.
- **Cons:** the stored model can go stale (retired, or disabled by an
  enterprise policy) until the user logs in again; older logins need a new
  login.
- **Effort:** M
- **Touches:** `harness`, `cli`
- **Outcomes:** meets all four.

### Option B: harness asks Copilot at every start

Nothing new is stored; the harness calls `/models` after the first token
exchange and uses the chat default.

- **Pros:** always the current default; older logins work as they are.
- **Cons:** an extra request at every start; no way to pin a model except the
  environment variable; the model does not come from env or disk.
- **Effort:** S
- **Touches:** `harness`
- **Outcomes:** meets the first two; fails `--model` on login; the error for
  older logins does not apply.

### Option C: a fixed default name

specworks ships a constant model id used with a stored login.

- **Pros:** smallest change, no request.
- **Cons:** fails when an enterprise disables that model; goes out of date.
- **Effort:** S
- **Touches:** `harness`
- **Outcomes:** meets the first only where the constant is allowed; fails
  `--model`.

## Recommendation

Option A, agreed with the user: the harness reads env, then files on disk,
and the login is where the model is chosen, from Copilot's own default unless
`--model` is given.

## Open Questions

- When `login` reuses a stored login that has no model, does it fill the model
  in, and does `--model` replace a stored model without `--force`? Proposed:
  yes to both. (who can answer: the user, in specify)
- Does `/models` give `is_chat_default` for both github.com and GHE logins,
  and what happens when no model is marked? (who can answer: checking against
  a live login, in specify or design)

## Candidate Capabilities

- `harness`: modified - the stored login also keeps a model, and the harness
  takes the model from `SPECWORKS_MODEL_MODEL`, else from the stored login
  (REQ-HARNESS-010, 011, 012).
- `cli`: modified - `specworks login copilot` gets `--model` and reports the
  stored model (REQ-CLI-023).
