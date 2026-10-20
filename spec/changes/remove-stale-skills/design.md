# Design: remove-stale-skills

## Context

`install_skills(root, tools)` (`src/specworks/tools/skills.py`) writes the
packaged skills and returns the files written, which `write_skills`
(`src/specworks/cli/project.py`) prints. See proposal.md for why stale skills
must go.

## Goals / Non-Goals

**Goals:**
- Remove stale specworks skills and prompt files from the chosen tools'
  folders, and report each one (REQ-INTEG-005).

**Non-Goals:**
- A manifest, and cleaning tools not chosen in the run.

## Decisions

### A separate `remove_stale_skills`, called before `install_skills`

`remove_stale_skills(root, tools) -> list[Path]` deletes, in each chosen tool's
skills folder, every folder named `specworks-*` or `sw-refine` that is not in
`packaged_skills()`. In its prompts folder, it deletes every
`<that name>.prompt.md`. It returns the deleted paths. `write_skills` calls it
first and prints `removed <path>` for each, then installs as today.

The alternative, having `install_skills` return both lists, would change a
signature for a second job. Keeping removal separate also keeps it testable on
its own. Serves: REQ-INTEG-005.

### Ownership is the name

Only names in specworks' namespace are candidates: the `specworks-` prefix,
plus `RETIRED_NAMES = ("sw-refine",)` for the one skill that predates it. A
folder or prompt file with any other name is never read or removed. Serves:
REQ-INTEG-005.

## Interfaces

- `src/specworks/tools/skills.py`: `remove_stale_skills(root: Path, tools: list[Tool]) -> list[Path]` (new)
- `src/specworks/tools/skills.py`: `RETIRED_NAMES: tuple[str, ...]` (new)
- `src/specworks/cli/project.py`: `write_skills` prints `removed <path>` before the `skill <path>` lines

## Risks / Trade-offs

- [A user's own `specworks-…` skill is deleted] -> the prefix is documented as
  specworks' own, and every deletion is printed, so it can be restored from
  git.
