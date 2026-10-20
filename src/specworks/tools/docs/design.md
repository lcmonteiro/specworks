# Design: integrations

## Overview

specworks' integrations with outside tools, in `src/specworks/tools`:
- **Diagrams** (`diagrams.py`): D2 sources in a `diagrams/` folder rendered to
  SVG through pyd2, with the workspace's shared settings, and a stamp that
  tells whether an SVG is still current.
- **Skills** (`skills.py`): the packaged agent skills (`src/specworks/skills`)
  installed for Claude Code and GitHub Copilot.

## Decisions

### SVGs carry a stamp, not a timestamp

Each generated SVG holds a hash of its source and render settings, right after
the XML declaration. Staleness is read from the stamp, not from file times,
which git doesn't keep. A hand-edited SVG has no matching stamp, so it reads as
stale. Checking needs no d2. The render options are part of the hash, so they
must stay stable. (baseline-integrations)

### pyd2 provides d2, `SPECWORKS_D2` overrides it

Rendering uses pyd2's pinned d2 release, so every user gets the same output.
`SPECWORKS_D2` names another program, which the tests use for a fake d2. Every
failure (no binary, a program that doesn't run, a compile error) becomes a
`DiagramError` naming the diagram, and so does an SVG that d2 wrote but that
can't be read or stamped (an unclosed `<?xml` declaration, non-UTF-8 output):
a render error for that diagram, never a crash, while the rest of the run
goes on. (baseline-integrations, diagram-bad-svg)

### One skill source, rendered per tool

Skills follow the Agent Skills format (`<name>/SKILL.md` with frontmatter).
Shared text lives once in `skills/_shared/` and is filled in at install time.
Each tool keeps only the frontmatter keys it understands, so Copilot drops
Claude Code's `allowed-tools`. The frontmatter is copied as text, line by line,
not through a YAML parser, so today's skills install byte-for-byte as written.
An indented line belongs to the key above it, so a multi-line value is kept or
dropped whole. Copilot also gets a prompt file per skill, so each phase is a
slash command. `auto` installs for the tools a project already uses, or for all
of them when none is detected. (baseline-integrations, skill-frontmatter-multiline)

### Stale specworks skills are removed by name

Before installing, specworks deletes from the chosen tools' folders every
skill folder and Copilot prompt file in its own namespace (the `specworks-`
prefix, or a retired name such as `sw-refine`) that it no longer ships, and
prints each one. Any other name is never touched, and a symlinked skill is
unlinked without following it. A manifest of installed files was rejected: it
would add a file to every project and miss the copies older versions already
left behind. (remove-stale-skills)

## Interfaces

- `src/specworks/tools/diagrams.py`: `Diagram`, `diagrams_in(folder)`,
  `state(diagram, settings) -> "ok" | "missing" | "stale"`,
  `render(diagram, settings)` (raises `DiagramError`), `find_d2()`,
  `referenced_images(markdown)`.
- `src/specworks/tools/skills.py`: `TOOLS`, `Tool`, `parse_tools(value, root)`
  (raises `ToolError`), `install_skills(root, tools) -> list[Path]`,
  `remove_stale_skills(root, tools) -> list[Path]`, `RETIRED_NAMES`,
  `packaged_skills()`, `read_skill(name)`.

## Constraints

- The render settings come only from the top-level config, so every diagram in
  the workspace shares one look.
- Skills are installed at the workspace root, never inside a module.
