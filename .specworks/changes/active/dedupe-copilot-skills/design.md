# Design: dedupe-copilot-skills

## Context

See proposal.md. Today `src/specworks/tools/skills.py` writes one folder per
chosen tool (`Tool.skills_dir`) plus Copilot prompt files
(`Tool.prompts_dir`, `render_prompt`); `installed_tools` infers the tools
from those folders, and `skills_state(root)` and `_stale_files` look only at
the folders of those tools. `src/specworks/cli/project.py` passes `--tools`
(default `"auto"`) to `init`, `skills` and `update`. The config
(`src/specworks/core/config.py`) refuses unknown keys, and `core` never
imports `tools` (`tools` imports `core`).

## Goals / Non-Goals

**Goals:**
- One rule, driven by a table, for which folders a set of tools needs.
- The saved `tools:` list is the source of truth once it exists; inference
  from the folders is only for projects that never saved one.

**Non-Goals:**
- Adding harnesses, or writing `.agents/skills/`.
- An interactive checklist widget: the question is one line of text.

## Decisions

### Each tool lists the folders it reads; the installer picks the fewest

`Tool` gains `reads: tuple[str, ...]`, with `skills_dir` (its preferred
folder) first: Claude Code `(".claude/skills",)`, Copilot
`(".github/skills", ".claude/skills", ".agents/skills")`. `skill_folders`
goes through the chosen tools in `TOOLS` order (Claude Code first) and gives
a tool its preferred folder only when no folder picked so far is in its
`reads`. Each folder's copy uses the frontmatter keys of the tool that owns
it. Alternative rejected: a special case for Claude Code + Copilot (Option B
of the refinement). Serves REQ-INTEG-005.

### No prompt files; the prompts folder is only cleaned

`prompts_dir` and `render_prompt` go. `PROMPTS_DIR = ".github/prompts"` stays
so that `specworks-…` (and `sw-refine`) prompt files are found and removed.
Stale copies are now looked for in the folders of every tool in `TOOLS`
(not only the chosen ones): a `specworks-…` folder is stale when it is not
shipped or its folder is not one `skill_folders` picked. A user's own names
are never touched. Serves REQ-INTEG-005, REQ-INTEG-006.

### The saved choice, resolved in one place

`resolve_tools(root, saved, given)` returns the tools and whether to save
them: `given` (`--tools`) wins and is saved; else `saved`; else
`installed_tools(root)`, else `auto`, saved. The CLI calls it in `init`,
`skills` and `update`, then saves with `save_tools` when asked. `--tools`
defaults to `None` (not `"auto"`) so "not given" can be told from an explicit
`auto`. Serves REQ-INTEG-004, REQ-CLI-009.

### Tool IDs known to core

`core/config.py` gets `TOOL_IDS = ("claude", "copilot")` to check `tools:`
without importing `tools`; a test checks that `TOOLS` has the same keys in the
same order. A module's config that sets `tools` is refused when the workspace
loads the module. Serves REQ-PROJ-003.

### Saving edits the config as text

`save_tools(root, ids)` in `core/config_file.py` replaces a `tools:` entry (a
flow list on one line, or a block list) or appends `tools: [a, b]` at the end,
like the other config edits (REQ-PROJ-008): it reloads the result and, when it
does not load with those tools, restores the file and raises `ConfigError`
saying to set `tools` by hand. Serves REQ-PROJ-022.

### The question at init

In `init`, before anything is written: when skills will be installed at a top
level, no `--tools` is given, the config (if any) saves no tools, and
`is_terminal()` is true, it asks once with `typer.prompt`:
`AI tools to install skills for (claude, copilot)`, default the detected tools
(`auto`) as a comma list. The answer goes through `parse_tools`, so an unknown
or empty list fails like `--tools` and nothing is written. `is_terminal()`
(`sys.stdin.isatty()`) is its own function so tests can replace it.
Serves REQ-CLI-003.

## Interfaces

Agreed with the user

Stubs in the design phase: `Tool.reads` gets a default of `()` (the dataclass
fields after `skills_dir` all have defaults) and is filled in for both tools in
`TOOLS`; `Config.tools` defaults to `None`. `Tool.prompts_dir` and
`render_prompt` stay until the code half removes them (task 2.3), since today's
tests and `expected_skills` use them. `ToolsOpt` defaults to `None` now, and
`init` and `skills` read `None` as `"auto"` until the code half replaces that
with `resolve_tools` (task 3.3), so today's behaviour is kept.

- `src/specworks/tools/skills.py`:
  - `Tool.reads: tuple[str, ...]` (preferred folder first); `Tool.prompts_dir` removed (REQ-INTEG-005)
  - `PROMPTS_DIR = ".github/prompts"` (REQ-INTEG-005)
  - `skill_folders(tools: list[Tool]) -> list[tuple[Tool, str]]`: the folders to write and the tool whose keys each copy keeps (REQ-INTEG-005)
  - `expected_skills(tools: list[Tool]) -> dict[str, str]`: now from `skill_folders`, no prompt files (REQ-INTEG-005, REQ-INTEG-006)
  - `resolve_tools(root: Path, saved: list[str] | None, given: str | None) -> tuple[list[Tool], bool]`: the tools and whether to save them (REQ-INTEG-004, REQ-CLI-009)
  - `skills_state(root: Path, saved: list[str] | None = None) -> SkillsState` (REQ-INTEG-006)
  - `remove_stale_skills(root: Path, tools: list[Tool]) -> list[Path]`: same signature, wider search (REQ-INTEG-005)
  - `render_prompt` removed
- `src/specworks/core/config.py`: `TOOL_IDS: tuple[str, ...]`; `Config.tools: list[str] | None` (REQ-PROJ-003)
- `src/specworks/core/config_file.py`: `save_tools(root: Path, ids: list[str]) -> None`, raises `ConfigError` saying to set `tools` by hand, with the file restored, when the edited config does not load with `ids` (REQ-PROJ-022)
- `src/specworks/cli/output.py`: `ToolsOpt` defaults to `None`; help names the saved choice (REQ-INTEG-004)
- `src/specworks/cli/project.py`: `is_terminal() -> bool`; `init`, `skills`, `update` resolve and save the tools (REQ-CLI-003, REQ-CLI-009)
- Config file: top-level `tools: [claude, copilot]` (REQ-PROJ-003, REQ-PROJ-022)

## Risks / Trade-offs

- [Copilot rejects `allowed-tools` in the `.claude/skills/` copy] -> not
  expected (the Agent Skills standard lists it); if it happens, Copilot with
  Claude Code gets its own `.github/skills/` copy again by changing Copilot's
  `reads`, one line.
- [JetBrains Copilot has no skill slash commands] -> out of scope; the skills
  still load by description.
- [A project's `.github/` copies vanish on upgrade] -> each removal is
  printed, and only `specworks-…` names are touched.

## Migration / Rollback

Projects upgrade with `specworks update` (or `skills`): the tools are inferred
once from the installed folders, saved, and the copies no longer needed are
removed. Rolling back to an older specworks: delete `tools:` from the config
(the older version refuses it as an unknown key) and run `specworks skills`.

This repository: `tests/test_skills.py` and `tests/test_cli.py` assertions on
prompt files change with REQ-INTEG-005; CLAUDE.md's line about refreshing
`.github/skills/` and `.github/prompts/` changes once they are gone.

## Open Questions

- None that change the specs or tasks.
