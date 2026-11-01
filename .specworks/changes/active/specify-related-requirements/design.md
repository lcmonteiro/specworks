# Design: specify-related-requirements

## Context

`describe` and `workspace_capabilities` (`src/specworks/specs/capabilities.py`)
read every capability's living spec with `read_spec`; a parsed
`Requirement` knows its header `line` and its last line `end` in the file.
`spec show` / `spec list` live in `src/specworks/cli/specs.py`. See
proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- A deterministic search over living requirements, for every module.
- Specify uses it, and the proposal records each match.

**Non-Goals:**
- Searching deltas; fuzzy or regex matching; a `check` warning.

## Decisions

### Matching

Terms are compared with `casefold()` as plain substrings. A requirement's
block is its file lines from its header (`line`) to `end`; the first line in
that range that contains any term is its match (the header counts, so a term
in the title matches the header line). A requirement is listed once however
many terms match. Capabilities come in `workspace_capabilities` order;
requirements in file order. A capability whose living spec does not exist
is skipped. A term that is empty after `strip()` raises `ConfigError`:
`empty search term`. Serves: REQ-SPECS-016.

### The result

`RequirementMatch(capability: str, id: str | None, title: str, path: str,
line: int, text: str)`: `path` relative to the workspace root (`ws.rel`),
`line` 1-based, `text` the matching line stripped. Serves: REQ-SPECS-016.

### The command

`spec find <term>... [--json]` (`terms: list[str]`, at least one: none is
`give at least one term`). Text: one line per match,
`<capability>  <ID>  <title>  <path>:<line>`; none prints
`no requirement mentions <terms joined by ", ">`. JSON:
`{"terms": [...], "matches": [{"capability", "id", "title", "path",
"line", "text"}]}`. Errors through `fail`/`ConfigError` like the other
commands. Serves: REQ-CLI-016.

### The proposal and the specify skill

Not requirements (template, instruction and skill text have no
capability); checked by wording tests.

- `src/specworks/templates/proposal.md` gains, after `## Capabilities`:
  `## Related requirements` with the comment
  `<!-- REQ-… modified, or REQ-… left: <reason>; None when spec find found none -->`.
- The proposal instruction in `src/specworks/schema.yaml` gains the bullet
  `- **Related requirements**: every living requirement that \`specworks spec find\` returns for the change's commands, flags, config keys and file names, as \`REQ-… modified\` or \`REQ-… left: <reason>\`; \`None\` when there is none.`
- `specworks-specify` step 2 gains, after the `spec show` / `spec list`
  block, the paragraph pinned below; step 5 lists the related requirements
  under the table.

### Pinned wording

Verbatim, in `src/specworks/skills/specworks-specify/SKILL.md`:
- ``specworks spec find "<term>" ... --json``
- `a MODIFIED block in the delta, or a one-line reason to leave it`
- `` `## Related requirements` ``
- `the related requirements, each modified or left with its reason`

In `src/specworks/templates/proposal.md`: `## Related requirements`.
In `src/specworks/schema.yaml`: `**Related requirements**`.
Messages: `empty search term`, `give at least one term`,
`no requirement mentions`.

## Interfaces

- `src/specworks/specs/capabilities.py`: `RequirementMatch` (dataclass) and
  `find_requirements(ws: Workspace, terms: list[str]) -> list[RequirementMatch]`,
  raising `ConfigError` (REQ-SPECS-016).
- `src/specworks/cli/specs.py`: `spec_find(terms: list[str] = typer.Argument(None), as_json: bool = JsonOpt) -> None`
  as `spec find` (REQ-CLI-016).

## Diagrams

No structural change: a function and a command in existing modules.

## Risks / Trade-offs

- [a short term matches many requirements] -> the agent picks specific
  terms (a command with its flag, a key name); the decision per match stays
  with the agent and the user.

## Open Questions

None.
