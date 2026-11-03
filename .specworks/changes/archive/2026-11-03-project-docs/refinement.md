# Refinement: project-docs

## Problem

A project or module has no document of the whole system: which capabilities it
has, how they interact and which decisions span them. Each capability's docs
describe only that capability, so a person new to the project, or an agent
starting a change, reads several capabilities' docs and their code to find how
the pieces connect, which is slow and costs agents tokens on every change.
This is the second half of the request that also gave `capability-tests`.

## Outcomes

- Every project and module has `<root>/docs/architecture.md`, of about 150
  lines at most, with: an Overview; the capabilities and how they interact (one
  line each, what each uses or gives, modules as one block linking to their own
  architecture) with a block diagram `docs/diagrams/architecture-blocks.d2`
  rendered to SVG; the architectural decisions that span capabilities (each
  with why and the change that made it); and a Glossary (one name per term).
- Close keeps it current: on every close the close skill checks it against the
  change and updates it when the change adds or removes a capability, changes
  what flows between capabilities, adds a cross-capability decision or a term;
  otherwise it stays as it is. When it is missing, that close writes the first
  one; `/specworks-adopt` and `/specworks-start` write it once the capabilities
  are mapped.
- `specworks close` fails when the change's module has no `docs/architecture.md`;
  `validate` warns when its diagram's SVG is out of date.
- The skills read it first: refine (before exploring), specify (before choosing
  capabilities and related requirements), design (before an API that crosses
  capabilities), review (when the change touches several capabilities) and
  onboard; with no file yet they go on without it.
- `specworks context` shows the docs folder of the project and of each module.

## Context

**Observed:**
- Capability living docs are `<capability path>/<docs_dir>/` (`docs_dir`
  default `docs`): `spec.md` and `requirements.md` written by `specworks close`
  (`src/specworks/specs/merge.py`), `design.md` and `diagrams/<cap>-blocks.d2`
  written by the close skill (`src/specworks/skills/specworks-close/SKILL.md`).
- Nothing exists at the project or module level; this repo has no root `docs/`.
- `specworks diagrams --dir <dir>` already renders `<dir>/diagrams/*.d2`;
  validate's `diagrams_current` checks only the change folder's diagrams.
- REQ-PROJ-016 refuses two capabilities sharing a docs folder; a capability on
  path `.` would have the same folder as the project's `docs/`.
- `specworks context --json` already lists every capability with its paths,
  prefix and test folder, so the architecture does not repeat that list.
- User-facing documentation lives in the GitHub wiki (CLAUDE.md); this file is
  living design for developers and agents, like a capability's `design.md`.

**Assumed:**
- One short file read at the start of a phase costs agents less than reading
  several capabilities' docs and code.

## Constraints

- [hard] The architecture is written by the close skill (judgement), never by
  hand outside close, like `design.md`.
- [hard] Existing projects keep working: the first close after this change
  writes the missing file instead of failing on it.
- [hard] Skill text is edited in `src/specworks/skills/` and installed with
  `specworks skills`; `tests/test_skills.py` pins wording.
- [soft] About 150 lines: the close skill merges or drops entries rather than
  growing the file.

## Options

### Option A: one architecture.md, read by every phase (chosen)

As in the outcomes: one file with Overview, interactions and diagram,
decisions and glossary; the close skill keeps it; the CLI checks it exists at
close, warns on a stale diagram, and shows the docs folder.

- **Pros:** one short file to load and keep current; the index of capabilities
  stays in `specworks context`, generated and never stale.
- **Cons:** the content depends on the close skill's judgement.
- **Effort:** M
- **Touches:** project, workflow, cli, plus the skills' text
- **Outcomes:** meets all.

### Option B: architecture.md plus a generated capabilities.md

A CLI-generated index of the capabilities (what, why, paths) next to the
architecture.

- **Pros:** a deterministic list in the docs folder.
- **Cons:** repeats `specworks context`; a second file to read; dropped by the user.
- **Effort:** M
- **Touches:** project, specs, workflow, cli
- **Outcomes:** meets all, with a redundant file.

### Option C: several files (glossary.md, conventions.md, ...)

- **Pros:** each concern in its own file.
- **Cons:** more to read and keep in sync; conventions are already the
  `context` text and CLAUDE.md.
- **Effort:** M
- **Touches:** as A
- **Outcomes:** meets all, at a higher reading cost.

## Recommendation

Option A, agreed with the user: one `architecture.md` with Overview,
capabilities and interactions with a block diagram, architectural decisions and
a Glossary; every phase reads it first; close keeps it current and writes it
when missing; the CLI checks it at close, warns on a stale diagram, and shows
the docs folder in `context`.

## Open Questions

- The folder: reuse `docs_dir` (`<root>/docs/`), and extend the unique docs
  folder check to a capability on `.`? Default assumed: yes. (who can answer:
  user, in specify)
- The top level's architecture shows each module as one block, linking to its
  own `docs/architecture.md`. Default assumed: yes. (who can answer: user, in specify)

## Candidate Capabilities

- `project`: modified - the project/module docs folder, its uniqueness against
  capability docs folders.
- `workflow`: modified - close fails without `docs/architecture.md`, validate
  warns on its stale diagram.
- `cli`: modified - `context` shows each project's and module's docs folder.
- The skills (no capability yet): close, adopt, start write it; refine,
  specify, design, review, onboard read it.
