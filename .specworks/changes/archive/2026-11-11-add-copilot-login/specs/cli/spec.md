# Spec Delta: cli

## ADDED Requirements

### Requirement: REQ-CLI-023 login

`specworks login copilot [--local | --global] [--force] [--ghe-host <host>]
[--json]` SHALL log in to GitHub Copilot (REQ-HARNESS-011) so that the harness
needs no key (REQ-HARNESS-012). The scope SHALL be global unless `--local` is
given; `--local` and `--global` together SHALL be a usage error, and `--local`
SHALL need a project and answer as REQ-CLI-001 does when there is none. The
verification address and the one-time code SHALL go to stderr, so that stdout
holds only the result. The result SHALL be `{"provider": "copilot", "scope":
"global" | "local", "reused": true | false}` with `--json`, or one line saying
the login was made or reused, without it. A provider other than `copilot` SHALL
fail naming `copilot`. Without the `harness` extra, it SHALL fail saying to
install `specworks[harness]`. Every failure SHALL be an error as REQ-CLI-001
describes, and no token SHALL appear in any output. No other command SHALL
import what login needs.

#### Scenario: AC-CLI-023.1 A global login by default

- **GIVEN** no stored login and a device flow that is authorised
- **WHEN** `specworks login copilot --json` runs, in a folder that is not a project
- **THEN** it exits 0 with `{"provider": "copilot", "scope": "global", "reused": false}`

#### Scenario: AC-CLI-023.2 A local login

- **GIVEN** a project and a device flow that is authorised
- **WHEN** `specworks login copilot --local --json` runs
- **THEN** it exits 0 with scope `local`, and the project's folder holds no new file

#### Scenario: AC-CLI-023.3 A login that exists is reused

- **GIVEN** a stored global login that still works
- **WHEN** `specworks login copilot --json` runs
- **THEN** it exits 0 with `"reused": true`, no device flow starts, and without `--json` the line says the login was reused

#### Scenario: AC-CLI-023.4 A forced login

- **GIVEN** a stored global login that still works
- **WHEN** `specworks login copilot --force --json` runs
- **THEN** a device flow runs and the result has `"reused": false`

#### Scenario: AC-CLI-023.5 The prompt on stderr

- **WHEN** `specworks login copilot --json` runs a device flow
- **THEN** stderr holds the verification address and the code, and stdout is one JSON document that holds neither

#### Scenario: AC-CLI-023.6 Both scopes

- **WHEN** `specworks login copilot --local --global` runs
- **THEN** it exits with the command line's usage error, and no flow starts

#### Scenario: AC-CLI-023.7 Local needs a project

- **WHEN** `specworks login copilot --local --json` runs where no specworks config is found
- **THEN** it exits 1 and its JSON has `"root": null`, and no flow starts

#### Scenario: AC-CLI-023.8 Another provider

- **WHEN** `specworks login github` runs
- **THEN** it exits 1 with an error naming `copilot`

#### Scenario: AC-CLI-023.9 A flow that fails

- **GIVEN** a device flow that is denied
- **WHEN** `specworks login copilot --json` runs
- **THEN** it exits 1 with `{"error": …}`, and no token appears in the output

#### Scenario: AC-CLI-023.10 Without the extra

- **GIVEN** the harness's dependencies cannot be imported
- **WHEN** `specworks login copilot` runs
- **THEN** it exits 1 and stderr says to install `specworks[harness]`

#### Scenario: AC-CLI-023.11 Other commands stay light

- **WHEN** `import specworks` and `specworks --help` run without the extra
- **THEN** they succeed, and neither chatinho, deepagents nor what login needs is imported

## MODIFIED Requirements

### Requirement: REQ-CLI-022 harness

`specworks harness`, with no argument or option, SHALL open the harness chat
(REQ-HARNESS-001) in the terminal for the current project, with an empty
conversation, and SHALL say nothing for the user: the user starts or continues
a change by sending a message to a peer, such as `@refine <request>`. Without the `harness` extra,
it SHALL fail saying to install `specworks[harness]`, without naming a Python version. A
model setting missing (REQ-HARNESS-010) SHALL fail naming the variable before
the chat opens, and a missing key with no stored login SHALL say to run
`specworks login copilot`. Every failure SHALL be `error: …` on stderr with exit 1. No
other command SHALL import the harness or its dependencies.

#### Scenario: AC-CLI-022.1 Without the extra

- **GIVEN** chatinho or deepagents cannot be imported
- **WHEN** `specworks harness` runs
- **THEN** it exits 1 and stderr says to install `specworks[harness]`, and names no Python version

#### Scenario: AC-CLI-022.2 No key

- **GIVEN** the extra installed, `SPECWORKS_MODEL_API_KEY` unset and no stored login
- **WHEN** `specworks harness` runs
- **THEN** it exits 1 naming `SPECWORKS_MODEL_API_KEY` and saying to run `specworks login copilot`, and no chat opens

#### Scenario: AC-CLI-022.5 Other commands stay light

- **WHEN** `import specworks` and `specworks --help` run without the extra
- **THEN** they succeed, and neither chatinho nor deepagents is imported

#### Scenario: AC-CLI-022.6 The chat opens with nothing said

- **WHEN** `specworks harness` builds its session and starts it
- **THEN** the conversation is empty and no peer runs until the user sends a message, such as `@refine add x`

#### Scenario: AC-CLI-022.7 No change option

- **WHEN** `specworks harness --change add-x` runs
- **THEN** it exits with the command line's usage error naming the unknown option, and no chat opens
