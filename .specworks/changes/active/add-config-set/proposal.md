# Proposal: add-config-set

## Why

Four skills (adopt, start, test, code) have the agent edit
`.specworks/config.yml` by hand to fill in `commands:` and `context:`, so a
broken block, a lost comment or a rejected key only shows at the next
command. Every other config write already goes through the CLI with a
reload-and-restore check; these two keys should too.

## What Changes

- New `specworks config set <key> [<value>] [--file <path>|-] [--module <name>] [--json]`.
  Keys: `commands.<test|lint|typecheck|build|format>` and `context`.
- A command is written as one line under `commands:` (replacing that key's
  line when there is one); `context` is written as a `context: |` block
  replacing the one there. An empty value clears the key.
- The config is edited as text, keeping comments and order, then reloaded:
  when it does not load with the new value, the original is restored and the
  error says to set it by hand. An unknown key, or a context over the size
  limit, is refused before anything is written.
- The adopt, start, test and code skills, and `_shared/phase-subagents.md`,
  use `specworks config set` instead of editing the YAML by hand.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `project`: adds REQ-PROJ-025 (setting `commands.<key>` and `context` in a
  config).
- `cli`: adds REQ-CLI-013 (the `config set` command).

## Impact

- `src/specworks/core/config_file.py`: a function that sets a config value.
- `src/specworks/cli/project.py` and `app.py`: the `config` command group
  with `set`.
- Skills: `specworks-adopt`, `specworks-start`, `specworks-test`,
  `specworks-code`, `_shared/phase-subagents.md`, and their installed copies.
- Tests: new tests for both requirements; skill wording tests.
- No new dependency; the config format is unchanged.

## Out of Scope

- Other keys (`docs_dir`, `diagrams.*`, `test_globs`, `source_globs`,
  `tools`): they stay hand-edited or keep their own commands.
- `config get`: `specworks context` already shows the commands and context.
- A round-trip YAML library.
