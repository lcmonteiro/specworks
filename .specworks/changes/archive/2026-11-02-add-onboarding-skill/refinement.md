# Refinement: add-onboarding-skill

## Problem

A person using specworks for the first time meets 13 skills, about 30 CLI
commands and a seven-phase flow, with no single entry point that says where
their project stands and what to do next. Picking the first skill
(`/specworks-start`, `/specworks-adopt` or `/specworks-refine`) is easy to get
wrong, and there is no skill to ask "what is a capability?" or "why did this
gate fail?" without reading the wiki.

## Outcomes

- A first-time user runs one skill, `/specworks-onboard`, and is told, from
  their real project, which state it is in (not set up, set up with no
  capabilities, changes in flight, ...) and the one next skill to run.
- The same skill explains the basic loop (refine → specify → build → done):
  what each step produces, the gates, and the ways back.
- The user can ask questions about specworks and about their own project and
  gets answers grounded in the installed CLI and the project's state, with a
  wiki link when they want more depth.

## Context

**Observed:**
- Skills live in `src/specworks/skills/specworks-*/SKILL.md`, with shared text
  in `_shared/` (asking-the-user, running-cli, ...). The installer
  (`src/specworks/tools/skills.py`) picks up every `specworks-*` folder, so a
  new skill folder is installed by `init`, `skills` and `update` with no code
  change.
- Skills reach a project only through `specworks init` / `skills` / `update`,
  so the onboarding skill exists only after `init` has run.
- The CLI already reports the state the skill needs: `specworks context`
  (root, capabilities with `hasSpec`, modules, changes, skills out of date),
  `status`, `gate`, `list`, and `--help` on every command.
- The README's Quick start lists the same first steps (start or adopt, then
  refine, specify, build, done); the wiki has Concepts, Tutorial, Skills, CLI
  and Reference pages.
- `tests/test_skills.py` checks skill wording verbatim; the skills have no
  capability, so skill-text changes are `skip-specs`.

**Assumed:**
- First-time users mostly run the skill right after `specworks init`, in a
  project that is set up but has no capabilities or changes yet.

## Constraints

- [hard] Skill text only: no CLI change, so the change is `skip-specs`.
- [hard] The skill never changes files: read-only tools (the CLI's read
  commands, Read, Grep, Glob); it points to the skill that does the work.
- [hard] Every stop ends with one closing question
  (`_shared/asking-the-user.md`).
- [hard] Works the same in Claude Code and Copilot, offline.
- [soft] The primer stays about one page; depth comes from wiki links, not
  copied text.

## Options

### Option A: Guide and answer (CLI first, short primer)

The skill reads `specworks context` (and `status`/`gate` when a change is
named) to say where the project is and which skill comes next, explains the
loop from a one-page primer (phases, capabilities, IDs and `@ac`/`@req` tags,
gates, the ways back), and answers questions from the CLI's output and
`--help`, the primer, and when needed an installed skill's own text, linking
the wiki page for depth.

- **Pros:** small; always matches the installed CLI; offline; no overlap with
  the skills that do the work.
- **Cons:** the primer can drift from the wiki; no hands-on practice change.
- **Effort:** S
- **Touches:** skills only (no capability)
- **Outcomes:** meets all three.

### Option B: Guided first change

Option A plus walking the user through a small practice change end to end,
running the other skills in order.

- **Pros:** hands-on learning.
- **Cons:** overlaps `/specworks-build` and `/specworks-done`; changes files;
  much larger.
- **Effort:** L
- **Touches:** skills only
- **Outcomes:** meets all three, beyond what was asked.

### Option C: Questions only, answered from the wiki

A specworks expert that fetches the wiki for each answer, with no state check
or walkthrough.

- **Pros:** most detailed answers.
- **Cons:** needs network and a fetch tool not every agent has; the wiki can
  disagree with the installed CLI; no "where am I".
- **Effort:** S
- **Touches:** skills only
- **Outcomes:** meets the third only.

## Recommendation

Option A, agreed with the user: a read-only `/specworks-onboard` that
diagnoses the project's state, explains the loop and answers questions, with
the CLI as the source of truth, a one-page primer, and wiki links for depth.

## Open Questions

- Should the README's Quick start point new users to `/specworks-onboard`?
  (who can answer: the maintainer, during specify)
- What the skill says when run outside a set-up project: likely "run
  `specworks init`, then `/specworks-start` or `/specworks-adopt`".
  (who can answer: the maintainer, during specify)

## Candidate Capabilities

- None: skills have no capability yet; the change is `skip-specs`.
