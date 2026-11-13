# Refinement: add-copilot-default-model

## Problem

`specworks login copilot` stores a working Copilot login, but `specworks
harness` still stops with `SPECWORKS_MODEL_MODEL is not set`. The stored
login can stand in for the API key, but not for the model name, so a user who
has just logged in still has to find a valid Copilot model id and export it
in every shell. A project also has no place to say which model its harness
uses, so the choice cannot be shared through the repository.

## Outcomes

- After `specworks login copilot` (with or without `--ghe-host`), running
  `specworks harness` starts with no `SPECWORKS_MODEL_*` variable set and no
  config edit, using Copilot's default chat model.
- A project can pin its model in `.specworks/config.yml`, with
  `specworks config set harness.model <id>`, and the harness uses it.
- `SPECWORKS_MODEL_MODEL`, when set, still wins over the config.
- When no model is named and Copilot gives no default, the harness stops
  before the session with an error saying to set `harness.model` or
  `SPECWORKS_MODEL_MODEL`.

## Context

**Observed:**
- `harness` capability (`src/specworks/harness`, docs in
  `src/specworks/harness/docs`): REQ-HARNESS-010 always requires
  `SPECWORKS_MODEL_MODEL`. REQ-HARNESS-012 lets a stored login replace only
  `SPECWORKS_MODEL_API_KEY` and the base URL.
- `model.py` `model_from_env` raises `ModelSettingsError(MODEL_NAME)` when the
  name is missing, even after it has found a stored login. It gets `root`, so
  it can reach the project's config.
- `copilot.py` `CopilotSession` exchanges the OAuth token for a session token
  and takes the API base from the exchange's `endpoints.api`.
- `project` capability (`src/specworks/core`): `.specworks/config.yml` holds
  `context`, `commands`, `branch_per_change` and `telemetry`;
  `config_file.py` `SETTABLE_KEYS` lists what `specworks config set` writes
  (REQ-PROJ-025), editing the file as text so comments stay.
- `cli` capability: `cli/harness.py` (REQ-CLI-022) fails naming the missing
  model variable; `cli/login.py` (REQ-CLI-023) is not affected.

**Assumed:**
- `GET <api base>/models` with the session token lists the models the login
  may use, each with an `id`, and marks Copilot's default chat model with
  `is_chat_default`. Community sources agree; the format is undocumented and
  not yet checked against a live github.com or GHE login.

## Constraints

- [hard] Environment variables win over the config, and the config wins over
  Copilot's default.
- [hard] An explicit `SPECWORKS_MODEL_API_KEY` still ignores the stored logins;
  with it, a model must come from the variable or the config (another provider
  has no default to ask for).
- [hard] No token appears in any output, error or file. The model id is not
  secret and may be shown.
- [hard] Configs without the new key still load unchanged.
- [soft] No request at startup when a model is named.

## Options

### Option A: config key, else Copilot's default

`harness.model` in `.specworks/config.yml`, set with `specworks config set`.
The harness takes the model from `SPECWORKS_MODEL_MODEL`, else the config,
else, with a stored login, asks Copilot's `/models` for its chat default after
the first token exchange.

- **Pros:** login then harness works in any project; a team pins a model in
  the repository; the default is always one the login may use.
- **Cons:** one extra request at startup when no model is named; depends on an
  undocumented field.
- **Effort:** M
- **Touches:** `project`, `harness`, `cli`
- **Outcomes:** meets all four.

### Option B: config key only

Same key, but no default: a missing model is an error naming the key.

- **Pros:** simple, explicit, no extra request.
- **Cons:** every project needs a setup step after login.
- **Effort:** S
- **Touches:** `project`, `harness`, `cli`
- **Outcomes:** fails the first; meets the others.

### Option C: login writes the project config

`login` asks Copilot for its default and writes it into the current project's
config.

- **Pros:** no request at harness start.
- **Cons:** a global login edits a project file; other projects get nothing.
- **Effort:** M
- **Touches:** `project`, `harness`, `cli`
- **Outcomes:** meets the first only for the project login ran in.

### Option D: model stored in the login file (dropped)

The earlier choice: the login keeps the model next to its token.

- **Pros:** no request at harness start.
- **Cons:** the model lives outside the project and cannot be shared;
  dropped once the model was wanted in the project config.
- **Effort:** M
- **Touches:** `harness`, `cli`
- **Outcomes:** fails the second.

## Recommendation

Option A, agreed with the user: the model is named by the environment or the
project config, and Copilot's own default fills the gap so login then harness
just works.

## Open Questions

- Does `/models` give `is_chat_default` for both github.com and GHE logins?
  When it marks none, or cannot be read, the harness fails as the last outcome
  says. (who can answer: checking against a live login, in design)

## Candidate Capabilities

- `project`: modified - the config gets `harness.model`, settable with
  `specworks config set` (REQ-PROJ-025).
- `harness`: modified - the model comes from `SPECWORKS_MODEL_MODEL`, else the
  config, else Copilot's default chat model for a stored login
  (REQ-HARNESS-010, REQ-HARNESS-012).
- `cli`: modified - `specworks harness`'s missing-model error names the config
  key too (REQ-CLI-022).
