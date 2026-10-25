# Proposal: remove-stale-skills

## Why

`specworks init` and `specworks skills` never remove skills a newer specworks
stopped shipping. Five renamed skills (`sw-refine`, `specworks-propose`,
`specworks-interface`, `specworks-implement`, `specworks-verify`) stay behind
in older projects, where an agent can load them and follow outdated steps
(suspected bug 9 of `baseline-integrations`; refinement.md, option A).

## What Changes

- On install or refresh, for each chosen tool, each `specworks-*` skill folder
  and Copilot `specworks-*.prompt.md` that is no longer shipped is deleted, as
  is the pre-prefix `sw-refine`.
- Each removal prints a `removed <path>` line, next to the existing
  `skill <path>` lines.
- Skills and prompt files under any other name, and the folders of tools not
  chosen, are never touched.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `integrations`: REQ-INTEG-005 "Installing the skills" MODIFIED. Its
  description adds the removal of stale specworks skills, and it gets a new
  criterion, AC-INTEG-005.6.

## Impact

- `src/specworks/tools/skills.py`: `install_skills` and a new helper that
  finds stale skills.
- `src/specworks/cli/project.py` (`write_skills`): prints the removals.
- `tests/test_skills.py`.

`install_skills` gains a way to report what it removed (settled in design). No
new dependency or config.

## Out of Scope

- A manifest of installed skills (option B).
- Removing skills of tools not chosen in this run (e.g. `--tools claude` leaves
  `.github/` alone).
