# Proposal: run-unknown-key

## Why

`specworks run <key>` with a key that is not a command key tells the user to
add it under `commands:`, which the config then refuses, so every command
fails to load (reproduced; suspected bug 12 of `baseline-cli`; refinement.md,
option A).

## What Changes

- Running a key other than `test`, `lint`, `typecheck`, `build` or `format`
  fails with `unknown command '<key>'` and the list of valid keys, before
  anything runs.
- A valid key that is not configured keeps its message, with an example for
  that key (`lint: <command>`) instead of always `test: uv run pytest`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: REQ-PROJ-013 "Running the project's commands" MODIFIED. Its
  description says an unknown key is refused naming the valid keys, and it
  gets a new criterion, AC-PROJ-013.4.

## Impact

`src/specworks/core/runner.py` (`run_command`) and its tests. `specworks run`
and the gates both go through it. No API, data or dependency change.

## Out of Scope

- Custom command keys (option C).
- A fixed choice list on the `run` argument (option B).
