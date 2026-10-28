# Spec Delta: integrations

## MODIFIED Requirements

### Requirement: REQ-INTEG-004 Choosing the AI tools

The system SHALL install skills for the tools given as `auto` (the tools the
project already uses, or every tool when none is detected), `all`, or a comma
list of tool IDs (`claude`, `copilot`). An unknown tool, or an empty list, SHALL
be refused before anything is written. When no tools are given, it SHALL use
the tools saved in the config, and, with none saved, the tools whose skills
are installed, else `auto`. Tools given with `--tools` to `specworks skills`
SHALL be saved in the config, and so SHALL the tools it used when the config
had none saved.

#### Scenario: AC-INTEG-004.1 Nothing detected

- **WHEN** a project that uses no supported tool is initialised
- **THEN** skills are installed for Claude Code and Copilot

#### Scenario: AC-INTEG-004.2 Detected tools

- **WHEN** the project has `.github/copilot-instructions.md`, or `CLAUDE.md`
- **THEN** skills are installed only for that tool

#### Scenario: AC-INTEG-004.3 Unknown tool

- **WHEN** an unknown tool (e.g. `cursor`) is given
- **THEN** the command fails with `unknown tool 'cursor'` and nothing is written

#### Scenario: AC-INTEG-004.4 No tool

- **WHEN** the tool list is empty (e.g. `,`)
- **THEN** it is refused with `no tool given`

#### Scenario: AC-INTEG-004.5 The saved tools

- **GIVEN** a project whose config saves `tools: [copilot]` and which has a `CLAUDE.md`
- **WHEN** `specworks skills` runs without `--tools`
- **THEN** skills are installed for Copilot only

#### Scenario: AC-INTEG-004.6 --tools changes the saved tools

- **GIVEN** a project whose config saves `tools: [claude]`
- **WHEN** `specworks skills --tools claude,copilot` runs
- **THEN** the config saves `tools: [claude, copilot]` and the skills are installed for both

#### Scenario: AC-INTEG-004.7 No saved tools yet

- **GIVEN** a project whose config has no `tools` and which has only Claude Code skills installed
- **WHEN** `specworks skills` runs without `--tools`
- **THEN** it installs for Claude Code and the config then saves `tools: [claude]`

### Requirement: REQ-INTEG-005 Installing the skills

The system SHALL write every packaged skill, with its shared parts filled in,
to the fewest skills folders that every chosen tool reads: each tool has a
folder it prefers (Claude Code `.claude/skills/`, Copilot `.github/skills/`)
and reads others too (Copilot also reads `.claude/skills/` and
`.agents/skills/`), and a tool already covered by another chosen tool's
folder gets no folder of its own. Each copy SHALL keep only the frontmatter
keys of the tool whose preferred folder it is in, each with its whole value
(the indented lines that continue it included). It SHALL write no prompt
files. It SHALL remove every skill folder named `specworks-…` (or the older
`sw-refine`) that is not shipped or is in a skills folder no longer used, and
every prompt file named `specworks-…` (or `sw-refine`) in `.github/prompts/`,
report each removal, and leave every other name alone. Skills always go to
the workspace root and are refreshed by `specworks skills`.

#### Scenario: AC-INTEG-005.1 Every skill

- **WHEN** skills are installed for Copilot only, or for Claude Code only
- **THEN** every packaged skill, each named `specworks-…`, is in that tool's folder, and no prompt file is written

#### Scenario: AC-INTEG-005.2 Frontmatter per tool

- **WHEN** skills are installed for Copilot only, or for Claude Code
- **THEN** the copies in `.github/skills/` keep `name` and `description` but not `allowed-tools`; the copies in `.claude/skills/` keep `allowed-tools`

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

#### Scenario: AC-INTEG-005.7 A value over several lines

- **GIVEN** a skill whose frontmatter has a folded `description: >` over two indented lines (one containing `Use when:`) and a multi-line `allowed-tools`
- **WHEN** it is copied into `.github/skills/` and into `.claude/skills/`
- **THEN** both copies keep all the lines of `description`, the `.github/skills/` copy drops `allowed-tools` with all its lines, and single-line frontmatter is copied exactly as before

#### Scenario: AC-INTEG-005.8 Claude Code and Copilot together

- **WHEN** skills are installed for Claude Code and Copilot
- **THEN** every packaged skill is in `.claude/skills/` only: no `specworks-…` skill in `.github/skills/` and no prompt file

#### Scenario: AC-INTEG-005.9 Copies no longer needed

- **GIVEN** a project installed by an older specworks for both tools: `specworks-refine` in `.claude/skills/` and `.github/skills/`, `.github/prompts/specworks-refine.prompt.md`, and the user's own `.github/skills/my-skill/` and `.github/prompts/my.prompt.md`
- **WHEN** `specworks skills --tools claude,copilot` runs
- **THEN** `.github/skills/specworks-refine/` and `.github/prompts/specworks-refine.prompt.md` are removed, each printed as `removed <path>`, and `my-skill`, `my.prompt.md` and `.claude/skills/specworks-refine/` are kept

### Requirement: REQ-INTEG-006 Skills state

The system SHALL compare the files it would install for the project's tools
(the tools saved in the config, else those whose skills folder holds a
`specworks-…` skill) with the installed ones. The skills state SHALL be:
- `current` when they match;
- `outdated` when any differs, is missing, or is a `specworks-…` skill or
  prompt file it would remove (not shipped, in a skills folder no longer
  used, or any `specworks-…` prompt file), listing each such file with its
  reason (`changed`, `missing`, `stale`);
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

#### Scenario: AC-INTEG-006.3 A missing skill

- **GIVEN** installed skills for Copilot only where one skill folder was deleted
- **WHEN** the state is computed
- **THEN** it is `outdated` and lists its `SKILL.md` as `missing`

#### Scenario: AC-INTEG-006.4 A skill no longer shipped

- **GIVEN** installed skills plus a `specworks-propose` skill folder and a user's own `my-skill`
- **WHEN** the state is computed
- **THEN** it is `outdated`, lists `specworks-propose` as `stale`, and does not list `my-skill`

#### Scenario: AC-INTEG-006.5 No skills installed

- **GIVEN** a project initialised with `--no-skills`
- **WHEN** the state is computed
- **THEN** it is `none`

#### Scenario: AC-INTEG-006.6 Copies left by an older version

- **GIVEN** a project whose config saves `tools: [claude, copilot]`, with current skills in `.claude/skills/` plus `.github/prompts/specworks-refine.prompt.md` and `.github/skills/specworks-refine/`
- **WHEN** the state is computed
- **THEN** it is `outdated` and lists both as `stale`
