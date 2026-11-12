# Proposal: add-copilot-default-model

## Why

After `specworks login copilot`, `specworks harness` still stops because
`SPECWORKS_MODEL_MODEL` is not set: a login replaces the key but not the model
name, and a project has no place to record which model its harness uses.

## What Changes

- The top-level `.specworks/config.yml` accepts a `harness:` block with one
  key, `model` (a non-empty model id); a module's config may not set it.
- `specworks config set harness.model <id>` writes it, keeping comments; an
  empty value clears it; from a module it writes the top level's config.
- The harness takes its model from `SPECWORKS_MODEL_MODEL`, else
  `harness.model`, else, when it uses a stored Copilot login, the model the
  Copilot API marks as its chat default (`GET <api base>/models`,
  `is_chat_default`), asked after the first token exchange and only then.
- With no model from any of these, building the model fails before the
  session starts, naming `SPECWORKS_MODEL_MODEL` and `harness.model`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: REQ-PROJ-003 (the `harness` block's shape, top level only),
  REQ-PROJ-025 (the keys `config set` accepts), and new REQ-PROJ-035 (setting
  `harness.model`).
- `harness`: REQ-HARNESS-010 (where the model comes from, the error naming
  both settings), and new REQ-HARNESS-013 (Copilot's default chat model).
- `cli`: REQ-CLI-013 (`harness.*` always written to the top level's config)
  and REQ-CLI-022 (the missing-model error names both settings).

## Related requirements

- REQ-PROJ-001 left: finding the config is unchanged.
- REQ-PROJ-002 left: unknown keys are still refused; `harness` simply becomes a known key.
- REQ-PROJ-003 modified
- REQ-PROJ-006 left: the workspace of modules is unchanged.
- REQ-PROJ-009 left: `init`'s default config gains no new entry.
- REQ-PROJ-021 left: the old config layout is unrelated.
- REQ-PROJ-025 modified
- REQ-PROJ-029 left: the docs folder is unrelated.
- REQ-PROJ-030 left: the event log is unrelated.
- REQ-PROJ-032 left: telemetry settings are unchanged; harness gets its own requirement.
- REQ-INTEG-008 left: Langfuse settings are unrelated.
- REQ-INTEG-009 left: sending events is unrelated.
- REQ-CLI-003 left: `init` is unchanged.
- REQ-CLI-004 left: overview commands are unchanged.
- REQ-CLI-005 left: registering modules and capabilities is unchanged.
- REQ-CLI-012 left: `commit` is unrelated.
- REQ-CLI-013 modified
- REQ-CLI-016 left: `spec find` is unrelated.
- REQ-CLI-017 left: `config set` records no new event.
- REQ-CLI-018 left: `telemetry push` is unrelated.
- REQ-CLI-019 left: telemetry IDs are unrelated.
- REQ-CLI-022 modified
- REQ-CLI-023 left: `login` is unchanged; it stores no model.
- REQ-HARNESS-008 left: staying in the workspace is unrelated.
- REQ-HARNESS-010 modified
- REQ-HARNESS-011 left: the login is unchanged.
- REQ-HARNESS-012 left: it covers the key and base URL from a login, which do not change; the model now comes from REQ-HARNESS-010 and REQ-HARNESS-013.

## Impact

- `src/specworks/core/config.py` (the `harness` block), `config_file.py`
  (`SETTABLE_KEYS` and the text edit), `cli/config.py` (top-level routing).
- `src/specworks/harness/model.py` (the model order), `copilot.py` (listing
  the models with the session token).
- One extra HTTPS request at harness start, only with a stored login and no
  model named. No new dependency.

## Out of Scope

- Storing a model in the login file, or a `--model` option on `login`.
- Choosing or validating the model against `/models` when one is named.
- A model in a module's config, or a base URL or key in the config.
- Adding a `harness:` example to `init`'s default config.
- Picking a fallback model when Copilot marks none as default.
