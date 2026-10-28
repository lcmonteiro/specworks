# Spec Delta: project

## ADDED Requirements

### Requirement: REQ-PROJ-022 Saving the tools

The system SHALL save the AI tools a project uses as a `tools:` list of tool
IDs in the top level's config, editing it as text: the user's comments and
other entries SHALL be kept, and a `tools:` list already there SHALL be
replaced. When the edit would not give the expected config, it SHALL leave the
file unchanged and say to set `tools` by hand.

#### Scenario: AC-PROJ-022.1 Saved with the comments kept

- **GIVEN** a config with comments and no `tools`
- **WHEN** the tools `claude` and `copilot` are saved
- **THEN** the config has `tools: [claude, copilot]`, its comments are still there, and it loads with those tools

#### Scenario: AC-PROJ-022.2 Replaced

- **GIVEN** a config that saves `tools: [claude]`
- **WHEN** the tool `copilot` is saved
- **THEN** the config has one `tools:` entry, `tools: [copilot]`

#### Scenario: AC-PROJ-022.3 A list the text edit cannot replace

- **GIVEN** a config with two `tools:` entries
- **WHEN** the tool `copilot` is saved
- **THEN** the config file is unchanged and the error says to set `tools` by hand

## MODIFIED Requirements

### Requirement: REQ-PROJ-003 Config value checks

The system SHALL reject a config whose values have the wrong shape, with an
error naming the setting: paths that leave the project, globs that are not a
list of `*`/`?`/`**` patterns, a context that is not text or is larger than
51200 bytes, commands that are not a mapping of test, lint, typecheck, build or
format to a command string, diagram settings that are not a known theme, a
known layout (elk or dagre), a true/false sketch and a non-negative pad, and
`tools` that is not a non-empty list of known tool IDs or is set in a module's
config.

#### Scenario: AC-PROJ-003.1 Paths stay inside the project

- **WHEN** `docs_dir`, a capability path or a module path is absolute, contains `..` or is not a non-empty string
- **THEN** loading (or adding the entry) fails saying it must be a relative folder inside the project

#### Scenario: AC-PROJ-003.2 Globs

- **WHEN** `test_globs` or `source_globs` is a single string, holds a non-string, or uses `[..]` or `{..}`
- **THEN** loading fails with a message naming the key (for a single string, showing it as a list)

#### Scenario: AC-PROJ-003.3 Context

- **WHEN** `context` is not a string, or is larger than 51200 bytes
- **THEN** loading fails saying so

#### Scenario: AC-PROJ-003.4 Commands

- **WHEN** `commands` is not a mapping, or a command is not a string
- **THEN** loading fails naming `commands` (with the allowed keys) or `commands.<key>`

#### Scenario: AC-PROJ-003.5 Diagram settings

- **WHEN** `diagrams.theme` or `diagrams.dark_theme` is not a known theme, or `diagrams.pad` is not a non-negative number
- **THEN** loading fails naming the setting; `dark_theme: none` is accepted and means the light theme is used in dark mode too

#### Scenario: AC-PROJ-003.6 Tools

- **WHEN** `tools` is not a list, is empty, or holds an unknown tool (e.g. `cursor`)
- **THEN** loading fails naming `tools` and the known tool IDs

#### Scenario: AC-PROJ-003.7 Tools in a module

- **WHEN** a module's config sets `tools`
- **THEN** loading fails saying `tools` is set in the top level's config
