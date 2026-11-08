# Spec Delta: cli

## MODIFIED Requirements

### Requirement: REQ-CLI-022 harness

`specworks harness`, with no argument or option, SHALL open the harness chat
(REQ-HARNESS-001) in the terminal for the current project, with an empty
conversation, and SHALL say nothing for the user: the user starts or continues
a change by sending a message to a peer, such as `@refine <request>`. Without the `harness` extra, or on a Python older than 3.12,
it SHALL fail saying to install `specworks[harness]` on Python 3.12 or later. A
model setting missing (REQ-HARNESS-010) SHALL fail naming the variable before
the chat opens. Every failure SHALL be `error: …` on stderr with exit 1. No
other command SHALL import the harness or its dependencies.

#### Scenario: AC-CLI-022.1 Without the extra

- **GIVEN** chatinho or deepagents cannot be imported
- **WHEN** `specworks harness` runs
- **THEN** it exits 1 and stderr says to install `specworks[harness]` on Python 3.12 or later

#### Scenario: AC-CLI-022.2 No key

- **GIVEN** the extra installed and `SPECWORKS_MODEL_API_KEY` unset
- **WHEN** `specworks harness` runs
- **THEN** it exits 1 naming `SPECWORKS_MODEL_API_KEY`, and no chat opens

#### Scenario: AC-CLI-022.5 Other commands stay light

- **WHEN** `import specworks` and `specworks --help` run without the extra
- **THEN** they succeed, and neither chatinho nor deepagents is imported

#### Scenario: AC-CLI-022.6 The chat opens with nothing said

- **WHEN** `specworks harness` builds its session and starts it
- **THEN** the conversation is empty and no peer runs until the user sends a message, such as `@refine add x`

#### Scenario: AC-CLI-022.7 No change option

- **WHEN** `specworks harness --change add-x` runs
- **THEN** it exits with the command line's usage error naming the unknown option, and no chat opens
