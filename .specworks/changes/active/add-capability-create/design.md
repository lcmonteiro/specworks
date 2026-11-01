# Design: add-capability-create

## Context

`capability add` (`src/specworks/cli/project.py`) checks the ID prefix and
the docs folder, registers the capability with `add_capability_entry`, then
prints it. The start skill writes each new folder's `.gitkeep` by hand. See
proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- `--create` creates a missing code folder with an empty `.gitkeep`, after
  the capability is registered, and never touches an existing folder.
- The start skill uses it.

**Non-Goals:**
- Creating folders without the flag; a `scaffold` command; adopt, close and
  done.

## Decisions

### Where the folder is checked and created

The folder is `target.root / path` (the path as `validate_relative` returns
it, relative to the owning module's root). With `--create`, a folder that
exists as a file is refused right after the existing checks and before
`add_capability_entry`: `<folder> exists and is not a folder; give <name>
another --path`, where `<folder>` is relative to the workspace root. The
folder and `.gitkeep` are created after the capability is registered, so any
refusal of `capability add` (prefix, docs folder, a name that exists, a bad
path) creates nothing. A folder that exists (with or without files) is left
as it is. Serves: REQ-CLI-014.

### Creating it

`mkdir(parents=True, exist_ok=True)`, then `.gitkeep` written empty with
`write_text("", encoding="utf-8")`. Only a folder that did not exist gets a
`.gitkeep`. Serves: REQ-CLI-014.

### The output

The JSON gains `"created"`: the `.gitkeep` path relative to the workspace
root (`src/auth/.gitkeep`), or `null` when nothing was created. It is
present with or without `--create`. The text output adds a second line
`created <path>` when one was created. Serves: REQ-CLI-014.

### The start skill

Step 5 runs `capability add` with `--create` and no longer writes `.gitkeep`
by hand; the Boundary and Guardrails say the `.gitkeep` files come from
`--create`, and the Guardrails' list of commands also names `config set`
(added by add-config-set but missing from that list). Not covered by a
requirement (skills have no capability); checked by wording tests.

### Pinned wording

Skill text in `src/specworks/skills/specworks-start/SKILL.md` (the test half
asserts these phrases, the code half writes them, both verbatim, backticks
included):

- `specworks capability add <name> --path <folder> [--module <m>] --create --description "<one line>"`
- ``--create` creates the code folder with an empty `.gitkeep` so git keeps it``
- ``module add`, `capability add --create` and `config set``
- The file no longer contains ``write an empty `.gitkeep` ``.

Error message fragment (tests assert it): `exists and is not a folder`.

## Interfaces

Proposed: waiting for the user's agreement

- `src/specworks/cli/project.py`: `capability_add` gains
  `create: bool = typer.Option(False, "--create", help="Create the code folder with an empty .gitkeep when it does not exist.")`
  (REQ-CLI-014); its JSON output gains `created: str | None` (the
  `.gitkeep` path relative to the workspace root, or `null`; present with or
  without `--create`). Extended, not breaking: the option defaults to off and
  existing callers only see the extra `created` key.
- Errors: no new error type; a `--path` that exists as a file raises the
  existing `ConfigError` with `<folder> exists and is not a folder; give
  <name> another --path` (`{"error": ...}`, exit 1 under `--json`)
  (REQ-CLI-014).

## Diagrams

No structural change: one option on an existing command.

## Risks / Trade-offs

- [the folder is created but the command fails later] -> creation is the
  last step, after the config is written and reloaded.

## Open Questions

None.
