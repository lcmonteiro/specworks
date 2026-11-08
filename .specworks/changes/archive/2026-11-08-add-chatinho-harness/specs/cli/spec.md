# Spec Delta: cli

## ADDED Requirements

### Requirement: REQ-CLI-022 harness

`specworks harness [REQUEST] [--change REF]` SHALL open the harness chat
(REQ-HARNESS-001) in the terminal for the current project. With `REQUEST`, it
SHALL be said to the peer `refine` as the user's first message, or, with
`--change`, to the peer of that change's phase. With `--change`, the run SHALL be
on that change (REQ-HARNESS-009); an unknown change SHALL be refused as every
command refuses one (REQ-CLI-002). Without the `harness` extra, or on a Python
older than 3.12, it SHALL fail saying to install `specworks[harness]` on Python
3.12 or later. A model setting missing (REQ-HARNESS-010) SHALL fail naming the
variable before the chat opens. Every failure SHALL be `error: …` on stderr with
exit 1. No other command SHALL import the harness or its dependencies.

#### Scenario: AC-CLI-022.1 Without the extra

- **GIVEN** chatinho or deepagents cannot be imported
- **WHEN** `specworks harness "add x"` runs
- **THEN** it exits 1 and stderr says to install `specworks[harness]` on Python 3.12 or later

#### Scenario: AC-CLI-022.2 No key

- **GIVEN** the extra installed and `SPECWORKS_MODEL_API_KEY` unset
- **WHEN** `specworks harness "add x"` runs
- **THEN** it exits 1 naming `SPECWORKS_MODEL_API_KEY`, and no chat opens

#### Scenario: AC-CLI-022.3 The request goes to refine

- **WHEN** `specworks harness "add x"` builds its session
- **THEN** the user's first message is `add x`, addressed to `refine`

#### Scenario: AC-CLI-022.4 Continuing a change

- **GIVEN** a change `add-x` in phase `design` with a `chat.jsonl`
- **WHEN** `specworks harness "go on" --change add-x` builds its session
- **THEN** the session holds the earlier conversation, and `go on` is addressed to `build`

#### Scenario: AC-CLI-022.5 Other commands stay light

- **WHEN** `import specworks` and `specworks --help` run without the extra
- **THEN** they succeed, and neither chatinho nor deepagents is imported
