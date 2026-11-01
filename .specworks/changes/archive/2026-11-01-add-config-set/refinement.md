# Refinement: add-config-set

## Problem

Four skills (adopt, start, test, code) tell the agent to edit
`.specworks/config.yml` by hand to fill in `commands:` and `context:`. That
step is not deterministic: the agent can break the indentation of the
`context: |` block, drop the file's comments, or write a key the config
rejects (`commands.unit`), and the mistake only shows at the next command.
Every other config write (`module add`, `capability add`, `skills --tools`)
already goes through the CLI, which re-reads the file and restores it when
the edit did not load.

## Outcomes

- `specworks config set commands.test "uv run pytest"` writes the command:
  `specworks context` shows it, and the file keeps its comments.
- `specworks config set context "<text>"` (or with `--file`) replaces the
  context with a multi-line text, and the config still loads.
- A key or value the config rejects is refused with `{"error": ...}` and the
  file is left unchanged.
- adopt, start, test and code use the command: none of them edits the YAML
  by hand any more.

## Context

**Observed:**
- `src/specworks/core/config_file.py`: `_insert_entry` (used by
  `add_module_entry` and `add_capability_entry`) and `save_tools` edit the
  config as text, reload it, and restore the original with a `ConfigError`
  ("add it by hand") when the reload fails or loses entries.
- `src/specworks/core/config.py`: `COMMAND_KEYS = (test, lint, typecheck,
  build, format)`; `load_commands` drops empty values; `context` must be a
  string of at most `MAX_CONTEXT_BYTES` (50 KB). The default config written
  by `init` has `context: |` followed by an empty line and
  `commands:` with empty `test:` and `lint:`.
- `src/specworks/cli/project.py`: `module add` and `capability add`
  (`--module` picks the module) are the existing config-writing commands.
- Skills that edit the YAML by hand: `specworks-adopt` steps 2 (commands) and
  3 (context), `specworks-start` step 5 (context and commands, top level and
  each module), `specworks-test` and `specworks-code` step 1 (add
  `commands.test` when empty); `_shared/phase-subagents.md` names
  `commands:` as where the test command goes.
- Living docs: `src/specworks/core/docs` (project) and
  `src/specworks/cli/docs` (cli).

**Assumed:**
- Agents pass a multi-line context more reliably through `--file` (or stdin)
  than as one quoted argument.

## Constraints

- [hard] The user's comments and key order in the config are kept.
- [hard] The file is never left broken: an edit that does not reload with
  the new value is rolled back.
- [hard] Errors are values: `{"error": ...}` with exit 1 under `--json`.
- [hard] No new dependency.
- [soft] Output and options follow the other commands (`--module`, `--json`,
  paths relative to the workspace root).

## Options

### Option A: `config set` for `commands.<key>` and `context`

`specworks config set <key> [<value>] [--file <path>|-] [--module <name>]
[--json]`. Keys: `commands.test|lint|typecheck|build|format` (one line under
`commands:`) and `context` (a `context: |` block). An empty value clears the
key. Text edit, reload, restore on error, like `save_tools`.

- **Pros:** small, fully testable, no dependency; the same command can take
  more keys later.
- **Cons:** other keys (`docs_dir`, `diagrams.*`, globs) stay hand-edited.
- **Effort:** S
- **Touches:** project, cli, skills
- **Outcomes:** meets all four.

### Option B: generic `config set` with a round-trip YAML library

Any key path, written through ruamel.yaml, which keeps comments.

- **Pros:** every key is covered.
- **Cons:** a new dependency; lists and mappings (globs, capabilities) need
  rules per value type, and `capability add` / `module add` already cover
  the mappings.
- **Effort:** M
- **Touches:** project, cli, skills
- **Outcomes:** meets all four.

### Option C: separate `commands set` and `context set`

Two command groups, one per key.

- **Pros:** each command is simple.
- **Cons:** two new command groups, and every new key needs another one.
- **Effort:** S
- **Touches:** project, cli, skills
- **Outcomes:** meets all four.

## Recommendation

Option A, agreed with the user: it covers what the four skills need, adds no
dependency, and can grow key by key. Out of scope: other keys (`docs_dir`,
`diagrams.*`, the globs, `tools`), a `config get` (`specworks context`
already shows both values), and a YAML library.

## Open Questions

- None blocking the proposal.

## Candidate Capabilities

- `project`: modified - writing `commands.<key>` and `context` into the
  config as text, keeping comments, with rollback.
- `cli`: modified - the new `specworks config set` command.
