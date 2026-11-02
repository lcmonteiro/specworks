# Design: add-onboarding-skill

## Context

See `proposal.md`. Skills are Markdown with frontmatter in
`src/specworks/skills/specworks-*/SKILL.md`; shared text is pulled in with
`<!-- specworks:include <name> -->` and the installer picks up every
`specworks-*` folder. `tests/test_skills.py` reads skills with
`read_skill(name)` and `allowed_commands(name)`.

## Goals / Non-Goals

**Goals:**
- One read-only skill that diagnoses the project's state, explains the loop
  and answers questions, grounded in the installed CLI.

**Non-Goals:**
- Doing any phase's work, or writing any file.
- Copying the wiki into the skill.

## Decisions

### Read-only by construction

`allowed-tools` is exactly
`Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Read, Grep, Glob`
(no Write, no Edit, no git). The CLI pattern also allows writing commands,
so the skill text lists the read commands it runs and its guardrail forbids
the rest. Alternative: no Bash at all, reading `.specworks/` files directly;
rejected, the CLI is the source of truth the refinement chose.

### State from `specworks context --json`, checked in order

The first row that matches decides the next step:

| What the CLI shows | State | Next |
|---|---|---|
| `"root": null` | not a specworks project | `uv tool install git+https://github.com/lcmonteiro/specworks`, `specworks init`, then `/specworks-start` or `/specworks-adopt` (given, not run) |
| `skills.state` is not `current` | skills out of date | `specworks update` |
| `capabilities` is empty | set up, nothing mapped | `/specworks-start` when the repo has no code, `/specworks-adopt` when it has |
| a capability with `"hasSpec": false` | not baselined | `/specworks-baseline <capability>` |
| `changes` is not empty | work in flight | per change, from its phase (below) |
| otherwise | ready | `/specworks-refine <what you want>` |

Changes in flight, from `phase` (and `specworks gate <phase>` when it
matters):
- `refine`: `/specworks-specify <ref>` when `refinement.md` is done,
  else `/specworks-refine <ref>`;
- `specify`: `/specworks-specify <ref>` until `gate specify` passes, then
  `/specworks-build <ref>`;
- `design`, `implement`, `review`: `/specworks-build <ref>`;
- `validate`, `close`: `/specworks-done <ref>`.

Several rows can apply at once (skills out of date and changes in flight):
the skill reports each one and recommends the first.

### Answer order

1. The user's project and the installed CLI (`context`, `status`, `gate`,
   `check`, `trace`, `spec show|list|find`, `<cmd> --help`).
2. The primer in the skill.
3. An installed skill's own `SKILL.md`, for what a skill does step by step.
4. A wiki link for depth (no fetching).

When the CLI and the primer disagree, the CLI wins and the skill says so.

### Primer, one page

Sections in the skill: the flow (`refine → specify → build → done`, and
`refine → specify → design → implement (test | code) → review → validate → close`
behind it), what each step writes (the README's table, shortened),
capabilities and living docs (`<path>/docs/`), IDs and tags (`REQ-…`, `AC-…`,
`@req`, `@ac`), gates (`specworks gate <phase>`), the ways back (review
findings to the phase that owns them, validate failures naming their phase),
and the wiki pages (Concepts, Tutorial, Skills, CLI, Reference).

### Pinned wording

The test half asserts these and the code half writes them, verbatim:

- Frontmatter `name: specworks-onboard`; the `description` contains
  `first time`, `getting started`, `"onboard"` and `"specworks onboard"`.
- `allowed-tools` as in the first decision; it contains neither `Write` nor
  `Edit`.
- The body includes `<!-- specworks:include running-cli -->` and
  `<!-- specworks:include asking-the-user -->`.
- `This skill never changes files` (the phase-boundary line).
- `specworks context --json` (step 1).
- Each next step of the state table appears: `specworks init`,
  `specworks update`, `/specworks-start`, `/specworks-adopt`,
  `/specworks-baseline`, `/specworks-refine`, `/specworks-specify`,
  `/specworks-build`, `/specworks-done`.
- `the CLI wins`.
- The wiki base `https://github.com/lcmonteiro/specworks/wiki`.
- README Quick start, just before step 1:
  ``New to specworks? Run **`/specworks-onboard`**: it tells you where your project stands and what to run next, and answers your questions.``

## Interfaces

None: no API change. The surface is the new skill file
`src/specworks/skills/specworks-onboard/SKILL.md` and its pinned wording.

## Diagrams

No structural change.

## Risks / Trade-offs

- [the primer drifts from the wiki and the CLI] -> it stays short, defers to
  the CLI, and links the wiki instead of copying it.
- [`Bash(specworks:*)` allows writing commands] -> the skill lists the read
  commands and its guardrail forbids the rest.
- [the state table drifts when a skill is added] -> the wording test pins
  every next step it names.

## Open Questions

None.
