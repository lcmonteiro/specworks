# Spec Delta: integrations

## MODIFIED Requirements

### Requirement: REQ-INTEG-005 Installing the skills

The system SHALL write every packaged skill, with its shared parts filled in, to
each chosen tool's skills folder (`.claude/skills/<name>/SKILL.md`,
`.github/skills/<name>/SKILL.md`), keeping only the frontmatter keys that tool
understands. For Copilot, it SHALL also write a prompt file per skill
(`.github/prompts/<name>.prompt.md`) holding the description, agent mode and the
skill's instructions. In the same folders, it SHALL remove every skill folder and
prompt file named `specworks-…` (or the older `sw-refine`) that is no longer
shipped, report each removal, and leave every other name alone. Skills always
go to the workspace root and are refreshed by `specworks skills`.

#### Scenario: AC-INTEG-005.1 Every skill

- **WHEN** skills are installed for all tools
- **THEN** every packaged skill, each named `specworks-…`, is in each tool's folder, with a Copilot prompt file

#### Scenario: AC-INTEG-005.2 Frontmatter per tool

- **WHEN** skills are installed for Copilot, or for Claude Code
- **THEN** Copilot's copy keeps `name` and `description` but not `allowed-tools`; Claude Code's keeps `allowed-tools`

#### Scenario: AC-INTEG-005.3 Copilot prompt files

- **WHEN** skills are installed for Copilot
- **THEN** each prompt file's frontmatter has the description and `agent: agent` and no `name`, followed by the skill's instructions

#### Scenario: AC-INTEG-005.4 Shared parts

- **WHEN** skills are installed
- **THEN** no installed file keeps a `specworks:include` marker; the shared text is in its place

#### Scenario: AC-INTEG-005.5 Where and when

- **WHEN** a module is initialised, or `specworks skills` runs for another tool
- **THEN** the module gets no skills folder of its own, and the refresh writes the other tool's skills

#### Scenario: AC-INTEG-005.6 Skills that are no longer shipped

- **GIVEN** a project whose `.claude/skills/` and `.github/` hold `specworks-propose` and `sw-refine` (skill folders and Copilot prompt files) and a user's own `my-skill`
- **WHEN** `specworks skills --tools all` runs
- **THEN** the stale `specworks-propose` and `sw-refine` folders and prompt files are removed, each printed as `removed <path>`, and `my-skill` and every shipped skill are kept
