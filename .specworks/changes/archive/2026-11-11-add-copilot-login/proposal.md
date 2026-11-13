# Proposal: add-copilot-login

## Why

`specworks harness` needs a model key in the environment, and a user with a GitHub Copilot plan has none: Copilot's API takes a GitHub device-flow login and a short-lived session token. One command, `specworks login copilot`, lets the harness run on the user's Copilot plan, with nothing to export.

## What Changes

- New command `specworks login copilot [--local | --global] [--force] [--ghe-host <host>] [--json]`: runs GitHub's device flow, stores only the long-lived OAuth token (owner-only) and never prints a token. Global (the default) serves every project; local serves the current project only. A working login in the chosen place is reused, with no new authorisation; `--force` or a stale login does the flow again.
- The harness's model: when `SPECWORKS_MODEL_API_KEY` is unset, the stored login (local before global) supplies the key and the Copilot API base. The key is a session token exchanged from the OAuth token and refreshed while the chat runs. `SPECWORKS_MODEL_MODEL` stays required, and an explicit key still wins.
- A local login is kept in the user's config dir, keyed by the project's root path, never inside the project: the harness agents read the project's checkout.
- The "no key" error of `specworks harness` names `SPECWORKS_MODEL_API_KEY` and points to `specworks login copilot`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `harness`: REQ-HARNESS-010 modified (the key may come from a stored login); new REQ-HARNESS-011 (the Copilot login: device flow, storage, reuse) and REQ-HARNESS-012 (the model from a stored login).
- `cli`: REQ-CLI-022 modified (the no-key error mentions the login); new REQ-CLI-023 (`login`).

## Related requirements

- REQ-HARNESS-010 modified: the key's source widens to a stored login; the never-shown rule extends to the tokens.
- REQ-CLI-022 modified: the missing-key failure points to `specworks login copilot`; its other scenarios are unchanged.
- REQ-HARNESS-008 left: the shell's hidden variables are unchanged, and the login is stored outside the checkout the file tools may read.
- REQ-CLI-001 left: `login` follows the output and error conventions as they are.
- REQ-PROJ-030 left: no file is added to a `.gitignore`, as nothing is stored in the project.

## Impact

- Code: `src/specworks/harness` (a Copilot auth module: device flow, token store, session-token provider; `model.py`), `src/specworks/cli` (the `login` command, lazily imported like `harness`).
- Data: a login file in the user's config dir (`XDG_CONFIG_HOME`, `%APPDATA%` on Windows), owner-only.
- Dependencies: none new; `httpx` comes with the `harness` extra.
- Systems: GitHub's device-flow and Copilot token-exchange endpoints (the exchange is unofficial and may change).

## Out of Scope

- `logout`, other providers than `copilot`, exporting variables (`--env`).
- A stored default model (the user still sets `SPECWORKS_MODEL_MODEL`).
- Adopting tokens other tools keep (`~/.config/copilot_model/`, `github-copilot`).
- Hiding the stored login from a peer's shell: `ws_run` can read any file the user can, as it can today.
