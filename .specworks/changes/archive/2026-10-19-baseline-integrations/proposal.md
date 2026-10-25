# Proposal: baseline-integrations

## Why

Record the existing behaviour of `integrations` (`src/specworks/tools`):
rendering design diagrams with D2, and installing the packaged agent skills for
Claude Code and GitHub Copilot. Later changes can then MODIFY these requirements
instead of only ADDING them.

## What Changes

- No behaviour change. The behaviour `integrations` already has is written down
  as requirements, and the existing tests and code are tagged with `@ac` /
  `@req`.
- One new test covers a criterion that no test checks yet: an empty tool list
  is refused.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `integrations`: its first requirements, REQ-INTEG-001 to REQ-INTEG-005.

## Impact

Comment tags in `src/specworks/tools/*.py` and in `tests/test_diagrams.py`,
`tests/test_skills.py`, `tests/test_cli.py` and `tests/test_modules.py`, plus
one new test. No API, data or dependency change.

Other capabilities own the neighbouring behaviour:
- the `diagrams` command's options (`--change`, `--dir`, `--check`,
  `--themes`) belong to `cli`;
- reading diagram settings from the config belongs to `project`;
- checking the images design.md embeds belongs to `specs`.

## Out of Scope

**Not specified here: the rules in the skills' own text.** `tests/test_skills.py`
also checks what the packaged skills say: every CLI call they show exists, they
pre-approve only specworks and read-only git, their triggers name specworks,
adopt hands over to baseline, done validates before it closes, and so on. That
behaviour lives in `src/specworks/skills/**/*.md`, which `source_globs`
(`src/**/*.py`) doesn't scan, so it can't carry `@req` tags. Recording it is a
candidate for its own change: a `skills` capability on `src/specworks/skills`,
with `source_globs` extended to its markdown.

Suspected bugs and unclear behaviour, each a candidate for its own change:
- **A malformed XML declaration crashes the render.** `stamp()` looks for the
  end of an `<?xml` declaration with `str.index("?>")`. An SVG that starts with
  `<?xml` but never closes it raises a raw `ValueError` instead of a
  `DiagramError`.
- **Skills are never removed.** `install_skills` overwrites the packaged skills
  but leaves behind ones a newer specworks no longer ships (renamed or dropped
  skills keep their old copies).
- **Multi-line frontmatter values are dropped.** Frontmatter is copied line by
  line, keeping only `key: value` lines. A multi-line value (a folded
  `description: >`) would lose its continuation lines. The packaged skills use
  single lines today.
