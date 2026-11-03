# Proposal: project-docs

## Why

Nothing describes a project or module as a whole: its capabilities, how they
interact and the decisions that span them. People and agents read several
capabilities' docs and code to see how the pieces connect, on every change.
One short `docs/architecture.md`, kept current at close and read first by the
phases, gives them that picture.

## What Changes

- Every project and module has a docs folder, `<root>/<docs_dir>` (`docs` by
  default), holding `architecture.md` and its `diagrams/`. A capability on `.`
  shares it.
- `specworks context` shows each module's (and the top level's) `docsPath` and
  `hasArchitecture`.
- `specworks close` refuses a change whose module has no `docs/architecture.md`,
  before validate, writing nothing; `--dry-run` names it as missing.
- `specworks validate` warns, without blocking, about an outdated or missing
  SVG of a diagram in the module's `docs/diagrams/`.
- Skills (no capability yet; pinned wording in design.md):
  - a shared text gives the architecture's structure: Overview; Capabilities
    and how they interact, with the block diagram
    `docs/diagrams/architecture-blocks.d2`; Architectural decisions; Glossary;
    about 150 lines;
  - close checks it against every change, updates it when the change adds or
    removes a capability, changes what flows between capabilities, adds a
    cross-capability decision or a term, and writes it when it is missing,
    before `specworks close`; adopt and start write the first one;
  - refine, specify, design, review and onboard read it first, and go on
    without it when there is none.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: a project's docs folder (new requirement).
- `cli`: REQ-CLI-004 (`context` shows each module's docs folder) and
  REQ-CLI-007 (`close` refuses without the architecture).
- `workflow`: REQ-FLOW-013 (validate warns on an outdated architecture diagram).

## Related requirements

- REQ-PROJ-003 left: `docs_dir`'s checks already apply; no new key.
- REQ-PROJ-007 left: what a module inherits; matched on "context".
- REQ-PROJ-011 left: change phases; matched on "close".
- REQ-PROJ-016 left: unique docs folders between capabilities; the project's
  folder may be shared with a capability on `.` (REQ-PROJ-029.3).
- REQ-PROJ-020 left: where changes live; matched on "docs_dir"/"close".
- REQ-PROJ-024 left: committing a phase; close's commit is unchanged.
- REQ-PROJ-025 left: `config set`; no new key.
- REQ-SPECS-006, REQ-SPECS-007, REQ-SPECS-010, REQ-SPECS-012 left: deltas,
  IDs and trace; matched on "close"/"context".
- REQ-SPECS-013 left: merging at close is unchanged; the refusal is in close's
  command (REQ-CLI-007).
- REQ-SPECS-014 left: `check`'s diagram rules cover a change's own diagrams.
- REQ-FLOW-002, REQ-FLOW-014, REQ-FLOW-016 left: instructions, starting a
  phase, findings; matched on "close"/"context".
- REQ-INTEG-001, REQ-INTEG-002, REQ-INTEG-003 left: rendering already works on
  `specworks diagrams --dir docs`.
- REQ-CLI-001 left: output conventions apply as they are.
- REQ-CLI-004 modified: modules show `docsPath` and `hasArchitecture`.
- REQ-CLI-007 modified: close refuses without the architecture.
- REQ-CLI-008 left: `diagrams --dir` already renders a folder.
- REQ-CLI-011, REQ-CLI-012, REQ-CLI-013 left: finding, commit, config set.
- REQ-FLOW-013 modified: validate warns on the module's outdated architecture diagram.

## Impact

- `src/specworks/core/workspace.py` (a module's docs folder),
  `src/specworks/cli/project.py` (`context`), `src/specworks/cli/` close command,
  `src/specworks/workflow/validate.py` (the warning).
- Skills: `_shared/architecture.md` (new) included by close, adopt and start;
  reading lines in refine, specify, design, review and onboard; installed
  copies refreshed with `specworks skills`; `tests/test_skills.py` wording checks.
- This repo gets its first `docs/architecture.md` at this change's own close.

## Out of Scope

- A generated capability index (`capabilities.md`): `specworks context` has it.
- Separate glossary or conventions files.
- Checking the architecture's content or size with the CLI.
- Updating a parent module's architecture from a module's close (the close
  skill may, by judgement; the CLI checks only the change's own module).
