## ADDED Requirements

### Requirement: REQ-INTEG-006 Skills state

The system SHALL compare, for every tool whose skills folder holds a
`specworks-…` skill, the files it would install (skill files and Copilot
prompt files) with the installed ones. The skills state SHALL be:
- `current` when they match;
- `outdated` when any differs, is missing, or is a `specworks-…` skill or
  prompt file no longer shipped, listing each such file with its reason
  (`changed`, `missing`, `stale`);
- `none` when no tool has a `specworks-…` skill installed.

Only `specworks-…` names (and the older `sw-refine`) SHALL be considered; a
user's own skills are ignored.

#### Scenario: AC-INTEG-006.1 Up to date

- **WHEN** skills were just installed with `specworks skills`
- **THEN** the state is `current` with no files listed

#### Scenario: AC-INTEG-006.2 A changed skill

- **GIVEN** installed skills where `.claude/skills/specworks-refine/SKILL.md` was edited
- **WHEN** the state is computed
- **THEN** it is `outdated` and lists that file as `changed`

#### Scenario: AC-INTEG-006.3 A missing skill or prompt file

- **GIVEN** installed skills for all tools where one skill folder and one Copilot prompt file were deleted
- **WHEN** the state is computed
- **THEN** it is `outdated` and lists each as `missing`

#### Scenario: AC-INTEG-006.4 A skill no longer shipped

- **GIVEN** installed skills plus a `specworks-propose` skill folder and a user's own `my-skill`
- **WHEN** the state is computed
- **THEN** it is `outdated`, lists `specworks-propose` as `stale`, and does not list `my-skill`

#### Scenario: AC-INTEG-006.5 No skills installed

- **GIVEN** a project initialised with `--no-skills`
- **WHEN** the state is computed
- **THEN** it is `none`
