# Design: upgrade-project

## Context

`install_skills` and `remove_stale_skills` (`src/specworks/tools/skills.py`)
always rewrite every skill. The proposal needs two more things from them:
- what *would* be written, to compare with what is installed;
- writing only the differences.

`context` and the new `update` command (`src/specworks/cli/project.py`) both
use the comparison.

## Goals / Non-Goals

**Goals:**
- One source of truth for "the files this CLI installs", used for writing and
  for comparing.
- `context` stays fast and read-only.

**Non-Goals:**
- A CLI self-upgrade, config migration, or a version stamp.

## Decisions

### The expected files are rendered in memory

`expected_skills(tools)` returns `{relative path: text}` for every skill file
and Copilot prompt file, using the same `read_skill` / `render_skill` /
`render_prompt` as the install. `install_skills` is rebuilt on top of it, so
the comparison can never drift from what is written. The alternative was to
hash the files at install time and keep the hashes in a file. It was turned
down: one more file to keep in sync, and it misses hand edits.
Serves: REQ-INTEG-006, REQ-CLI-009.

### Stale files come from the existing name rule

`_stale` (already used by `remove_stale_skills`) decides which `specworks-…`
or `sw-refine` names are no longer shipped. The state and the removal share
it. Serves: REQ-INTEG-006.

### Which tools are checked and updated

`installed_tools(root)`: the tools whose skills folder holds at least one
`specworks-…` (or `sw-refine`) folder. `update` uses them by default and
falls back to `auto` (`parse_tools`) when there are none; `--tools` overrides
both. Serves: REQ-INTEG-006, REQ-CLI-009.

### Write only what differs

`update_skills(root, tools)` compares before writing: a file whose text
already matches is left untouched (so `update` on current skills writes
nothing), and stale files are removed with the existing
`remove_stale_skills`. `specworks skills` keeps calling `install_skills` and
rewrites everything, as before. Serves: REQ-CLI-009.

## Interfaces

- `src/specworks/tools/skills.py`:
  - `expected_skills(tools: list[Tool]) -> dict[str, str]`: relative path to
    rendered text, for every skill and Copilot prompt file of `tools`
    (REQ-INTEG-006).
  - `installed_tools(root: Path) -> list[Tool]`: the tools with a
    `specworks-…` skill installed (REQ-INTEG-006).
  - `SkillFile` (frozen dataclass): `path: str` (relative to the root) and
    `reason: Literal["changed", "missing", "stale"]` (REQ-INTEG-006).
  - `SkillsState` (frozen dataclass): `state: Literal["current", "outdated",
    "none"]` and `files: list[SkillFile]`, sorted by path (REQ-INTEG-006).
  - `skills_state(root: Path) -> SkillsState` (REQ-INTEG-006).
  - `update_skills(root: Path, tools: list[Tool]) -> tuple[list[Path],
    list[Path]]`: (updated, removed) (REQ-CLI-009).
- `src/specworks/cli/project.py`:
  - `specworks update [--tools auto|all|<list>]`: by default, the installed
    tools. Prints `tools <labels>`, then `updated <path>` / `removed <path>`
    per file, or `skills up to date` (REQ-CLI-009).
  - `specworks context`:
    - `--json` gains `"skills": {"state": "...", "files": [{"path": "...",
      "reason": "..."}]}`;
    - the text output gains a `skills:` line (`current`, `none`, or
      `outdated (N files)`) and, when outdated, the line
      `skills out of date: run specworks update` (REQ-CLI-004).

## Risks / Trade-offs

- [`context` renders every skill on each call] -> a dozen small files per
  tool, read from the package; measured as part of the code phase. Cache it
  if it shows.
- [A hand-edited skill shows as `outdated`] -> intended. The hint tells the
  user, and `update` restores the shipped text.
- [Line endings on Windows] -> files are written and read with
  `encoding="utf-8"` and compared as text, so newline translation does not
  count as a change.

## Open Questions

None.
