# Design: add-config-set

## Context

The config is edited as text everywhere the CLI writes it (`_insert_entry`
for modules and capabilities, `save_tools`), because a YAML dump would drop
the user's comments; each writer reloads the file and restores the original
when the edit did not give the expected config. `commands:` and `context:`
are the two keys the skills still write by hand. See proposal.md for the
motivation.

## Goals / Non-Goals

**Goals:**
- One function that sets `commands.<key>` or `context` the same safe way, and
  one command around it.
- The four skills and `_shared/phase-subagents.md` call the command.

**Non-Goals:**
- Other keys, `config get`, a YAML library.
- Rewriting flow-style entries (`commands: {test: pytest}`): those are
  refused with "set it by hand".

## Decisions

### The keys

`SETTABLE_KEYS` is `context` plus `commands.<key>` for every key of
`COMMAND_KEYS`, in that order. Any other key is refused before reading the
file: `unknown config key '<key>'; use one of: context, commands.test,
commands.lint, commands.typecheck, commands.build, commands.format`. A context
larger than `MAX_CONTEXT_BYTES` is refused before writing with the same
message `load_config` gives. Serves: REQ-PROJ-025.

### Writing a command

The top-level `commands:` line (`commands:`, or `commands: {}` with an
optional comment) opens the block; its indented and blank lines are the
block. A line `  <key>:` in the block is replaced; otherwise the entry goes
after the block's last indented line, keeping the order of addition. With no
`commands:` line, a blank line and a `commands:` block are appended. The line
is `  <key>: <value>` when YAML reads `<key>: <value>` back as exactly that
string, and `  <key>: <json-quoted value>` otherwise (a `#`, `: `, a leading
quote). An empty value writes `  <key>:`, the way `init` does, which the
config loads as no command. Serves: REQ-PROJ-025.

### Writing the context

The top-level `context:` line and the indented and blank lines after it are
the entry; trailing blank lines stay in place. It is replaced by
`context: |` and the text's lines indented by two spaces (blank lines stay
empty), with trailing newlines dropped from the text: the config then loads
the text plus one final newline. When the text's first line starts with a
space the header is `context: |2`, so YAML does not take that indent as the
block's. An empty text writes `context: |` alone. With no `context:` line,
the entry is appended. Serves: REQ-PROJ-025.

### The check after writing

Before writing, the file is parsed as YAML; after writing, it is loaded with
`load_config` and parsed again. The edit stands only when it loads and the
parsed mapping equals the one before with just that key set (for `context`,
the text plus one newline, or `None` when empty; for a command, the value, or
`None` when empty). Otherwise the original text is written back and the error
is `could not set <key> in <config path> automatically; set it by hand`. A
flow mapping such as `commands: {test: pytest}` gets a second `commands:`
block, the check sees `test` gone, and the file is restored. Serves:
REQ-PROJ-025.

### The command

`specworks config set <key> [<value>] [--file <path>] [--module/-m <name>] [--json]`
in a new `config` group. `--file -` reads standard input. Exactly one of
`<value>` and `--file` is needed: both is `give the value as an argument or
with --file, not both`, neither is `give a value, or --file <path> (- for
standard input)`; both are refused before anything is read or written. The
target is `ws.module(module)` when `--module` is given, else the current
module, as in `capability add`. Output: text `set <key> in <config path>`;
JSON `{"key", "value", "config", "module"}` with `config` relative to the
workspace root and `module` the module's label. Serves: REQ-CLI-013.

### The skills

adopt step 2 writes each confirmed command with the command; adopt step 3 and
start step 5 write the context through standard input; start writes a
module's with `--module`; test and code step 1 save the test command once the
user agrees; the phase-subagents table names the command. Not covered by a
requirement (skills have no capability); checked by wording tests.

### Pinned wording

Skill text (the test half asserts these phrases, the code half writes them,
both verbatim, backticks included):

- `specworks-test/SKILL.md` and `specworks-code/SKILL.md`: ``save it with `specworks config set commands.test "<command>"` ``
- `specworks-adopt/SKILL.md`: ``write each one with `specworks config set commands.<key> "<command>"` ``
- `specworks-adopt/SKILL.md` and `specworks-start/SKILL.md`: ``write it with `specworks config set context --file -` (the text on standard input)``
- `specworks-start/SKILL.md`: ``add `--module "<name>"` for a module's own config``
- `_shared/phase-subagents.md`: `` `specworks config set commands.test "<command>"` ``
- None of those five files contains ``under `commands:` `` or ``under `context:` ``.

Error messages (tests assert these fragments): `unknown config key`,
`use one of: context, commands.test`, `set it by hand`, `not both`,
`- for standard input`.

## Interfaces

Proposed: waiting for the user's agreement

- `src/specworks/core/config_file.py`: `SETTABLE_KEYS: tuple[str, ...]` (new),
  `("context", "commands.test", "commands.lint", "commands.typecheck", "commands.build", "commands.format")`
  (REQ-PROJ-025).
- `src/specworks/core/config_file.py`: `set_config_value(root: Path, key: str, value: str) -> None` (new),
  the config at `root` (a module root, like `add_capability_entry`); an empty
  `value` clears the key; raises `ConfigError` (existing) for an unknown key,
  a context over `MAX_CONTEXT_BYTES`, or an edit that does not load back
  (file restored) (REQ-PROJ-025).
- `src/specworks/cli/app.py`: `config_app = App(help="Set values in a module's config (.specworks/config.yml).")`
  (new), registered with `app.add_typer(config_app, name="config")`.
- `src/specworks/cli/project.py`: `config_set(key: str, value: str | None, file: str | None, module: str | None, as_json: bool) -> None`
  (new) as `@config_app.command("set")`: argument `key`, optional argument
  `value`, `--file` (`-` for standard input), `--module/-m`, `--json`;
  output text `set <key> in <config path>`, JSON
  `{"key", "value", "config", "module"}`; errors through `SpecworksError`
  (`{"error": ...}`, exit 1) (REQ-CLI-013).

No breaking change: existing functions and commands are untouched.

## Diagrams

No structural change: one function in `core/config_file.py` and one command
in `cli/project.py`, with the dependencies the other config writers already
have.

## Risks / Trade-offs

- [an unusual layout, e.g. `context: >` or a comment inside the block] ->
  the check after writing restores the file and says to set it by hand.
- [skill wording drifts from the tests] -> the pinned wording above.

## Open Questions

None.
