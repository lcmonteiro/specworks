# Proposal: add-onboarding-skill

## Why

A first-time user meets 13 skills, about 30 commands and a seven-phase flow
with no entry point that says where their project stands, what to run next,
or where to ask how specworks works. The refinement chose Option A: a
read-only skill that diagnoses, explains and answers.

## What Changes

- A new packaged skill `src/specworks/skills/specworks-onboard/SKILL.md`
  (`/specworks-onboard`), installed by `init`, `skills` and `update` like
  every other skill. It never changes files: `allowed-tools` holds only the
  specworks CLI, Read, Grep and Glob, and the skill runs only the CLI's read
  commands (`context`, `status`, `list`, `gate`, `check`, `trace`,
  `spec show|list|find`, `<cmd> --help`).
- **Where you are**: from `specworks context --json` (and `status`/`gate`
  for a change) it names the project's state and the one next skill:
  - not a specworks project (`"root": null`): the install command,
    `specworks init`, then `/specworks-start` or `/specworks-adopt`; it
    gives the commands and does not run them;
  - skills out of date: `specworks update`;
  - no capabilities: `/specworks-start` (no code yet) or `/specworks-adopt`
    (existing code);
  - a capability with no living spec: `/specworks-baseline <capability>`;
  - changes in flight: the skill that continues each one, from its phase;
  - otherwise: `/specworks-refine <what you want>`.
- **The basic loop**: a one-page primer in the skill: the flow
  `refine → specify → build → done` and the phases behind it, what each
  step writes, capabilities and living docs, requirement IDs and the
  `@ac`/`@req` tags, gates, and the ways back (review findings, validate
  failures).
- **Questions**: answered from the user's project and the installed CLI
  first (`context`, `status`, `gate`, `<cmd> --help`), then the primer, then
  an installed skill's own `SKILL.md` for "what does `/specworks-x` do?",
  with a link to the wiki page for depth. When the CLI and the primer
  disagree, the CLI wins.
- Every stop ends with the shared closing question
  (`_shared/asking-the-user.md`).
- The README's Quick start gains one line pointing new users to
  `/specworks-onboard`.
- Untagged wording checks in `tests/test_skills.py`, and the installed copies
  refreshed with `specworks skills`.

## Capabilities

None: only packaged skill text and the README change, and no capability
holds requirements for the skills. The change is marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Related requirements

- REQ-INTEG-004 left: choosing the AI tools does not depend on which skills exist.
- REQ-INTEG-005 left: "every packaged skill" already covers a new skill folder.
- REQ-INTEG-006 left: the skills state compares whatever skills are packaged.
- REQ-INTEG-007 left: the new skill uses existing includes with no new parameters.
- REQ-CLI-003 left: `init` installs the skills through REQ-INTEG-005, unchanged.
- REQ-CLI-004 left: the overview commands the skill reads keep their output.
- REQ-CLI-009 left: `update` refreshes every packaged skill, unchanged.
- REQ-PROJ-021 left: the old config layout is unrelated to the skills' text.

## Impact

- New `src/specworks/skills/specworks-onboard/SKILL.md`; `README.md`;
  `tests/test_skills.py`; the installed copy in `.claude/skills/`.
- No CLI, API or data change.

## Out of Scope

- A guided practice change run by the skill (refinement Option B).
- Fetching the wiki at answer time (refinement Option C).
- Running `specworks init` or any command that writes.
- Changing what `specworks init` prints to mention the skill (a CLI
  behaviour change, for its own change).
- The wiki's Skills page: the wiki lives outside this repo and is updated
  separately.
- Tagging and specifying skill text (still undecided for every skill).
