# Spec Delta: cli

## MODIFIED Requirements

### Requirement: REQ-CLI-003 init

`specworks init` SHALL create `.specworks/config.yml`,
`.specworks/changes/active/` and `.specworks/changes/archive/`, and
install the agent skills unless `--no-skills` is given. Inside a specworks
project, it SHALL link the new project as a module (named by its full path)
unless `--no-link` is given, and SHALL refuse a folder that holds a module of
the workspace (naming it) before writing anything. It SHALL refuse a folder
that is not inside a git repository, saying to run `git init`, before writing
anything. `--diagram-theme` SHALL apply only to a new top-level config;
elsewhere it SHALL print a note saying it wasn't applied. When it installs
skills at a top level whose config saves no tools and no `--tools` is given,
it SHALL ask which tools the project uses if it runs in a terminal, offering
the detected tools as the default, and SHALL use the detected tools (`auto`)
without asking otherwise; the tools it installs SHALL be saved in the config.

#### Scenario: AC-CLI-003.1 A new project

- **GIVEN** the folder is empty and inside a git repository
- **WHEN** `init` runs there
- **THEN** it creates `.specworks/config.yml`, `.specworks/changes/active/`, `.specworks/changes/archive/` and the skills

#### Scenario: AC-CLI-003.2 Inside a project

- **WHEN** `init <path>` runs inside a project (or a module)
- **THEN** the folder is linked as a module, named `parent/child` when nested, with no skills folder of its own

#### Scenario: AC-CLI-003.3 An independent project

- **WHEN** `init --no-link` runs inside a project
- **THEN** the folder isn't linked and is a top level of its own

#### Scenario: AC-CLI-003.5 A theme that cannot apply

- **WHEN** `--diagram-theme` is given for an existing project
- **THEN** init succeeds and says `--diagram-theme not applied`

#### Scenario: AC-CLI-003.6 A folder around an existing module

- **GIVEN** module `billing` at `services/billing`
- **WHEN** `init services` runs from the top level
- **THEN** it is refused naming module `billing`, nothing is written (no config, no link), and the workspace still loads

#### Scenario: AC-CLI-003.7 Outside a git repository

- **GIVEN** a folder that is in no git repository
- **WHEN** `init` runs there
- **THEN** it fails saying to run `git init`, and writes nothing (no config, no folder, no skills)

#### Scenario: AC-CLI-003.8 No --dir option

- **WHEN** `init --dir spec` runs
- **THEN** it fails as an unknown option and writes nothing

#### Scenario: AC-CLI-003.9 Asked in a terminal

- **GIVEN** a new project with a `CLAUDE.md`, and `init` running in a terminal without `--tools`
- **WHEN** the question lists `claude` and `copilot` with `claude` as the default, and the answer is `copilot`
- **THEN** skills are installed in `.github/skills/` only and the config saves `tools: [copilot]`

#### Scenario: AC-CLI-003.10 The default answer

- **GIVEN** a new project with a `CLAUDE.md`, and `init` running in a terminal without `--tools`
- **WHEN** the answer is empty
- **THEN** skills are installed for Claude Code and the config saves `tools: [claude]`

#### Scenario: AC-CLI-003.11 No terminal

- **GIVEN** a new project that uses no supported tool
- **WHEN** `init` runs with no terminal (as from CI or an agent)
- **THEN** nothing is asked, skills are installed in `.claude/skills/` only, and the config saves `tools: [claude, copilot]`

#### Scenario: AC-CLI-003.12 --tools or a saved choice

- **WHEN** `init --tools copilot` runs in a terminal, or `init` runs again in a project whose config saves tools
- **THEN** nothing is asked; the given tools are installed and saved, or the saved ones are installed

### Requirement: REQ-CLI-009 update

`update` SHALL bring the workspace's skills up to the running CLI. It refreshes
the tools saved in the config (`--tools` overrides them and is saved; with none
saved it uses the tools that have `specworks-…` skills installed, else `auto`,
as `skills` does, and saves them). It SHALL write only the files that differ or
are missing, printing `updated <path>` for each, and remove the stale ones,
printing `removed <path>`. When nothing needs a change, it SHALL write nothing
and print `skills up to date`. Run from a module, it SHALL update the workspace
root's skills.

#### Scenario: AC-CLI-009.1 Outdated skills

- **GIVEN** installed skills where one skill file was edited, another deleted, and a `specworks-propose` folder added
- **WHEN** `update` runs
- **THEN** it prints `updated` for the two files and `removed` for `specworks-propose`, and the skills state is then `current`

#### Scenario: AC-CLI-009.2 Already up to date

- **GIVEN** skills just installed
- **WHEN** `update` runs
- **THEN** it prints `skills up to date` and no installed file is rewritten

#### Scenario: AC-CLI-009.3 Keeps the installed tools

- **GIVEN** a project whose config saves no tools, with only Claude Code skills installed and a `.github/copilot-instructions.md`
- **WHEN** `update` runs
- **THEN** it refreshes the Claude Code skills, writes no Copilot skill or prompt file, and the config then saves `tools: [claude]`

#### Scenario: AC-CLI-009.4 From a module

- **WHEN** `update` runs inside a module's folder
- **THEN** the workspace root's skills are updated and the module gets no skills folder

#### Scenario: AC-CLI-009.5 Both tools, one folder

- **GIVEN** a project whose config saves `tools: [claude, copilot]` and whose skills were just installed
- **WHEN** `update` runs
- **THEN** it prints `skills up to date`, and there is no `specworks-…` skill in `.github/skills/`
