# Spec Delta: workflow

## MODIFIED Requirements

### Requirement: REQ-FLOW-008 Gate code

The code gate SHALL check the code half of implement: it SHALL require every
`[code]` task done, `@req` code for every requirement, no unknown tags, no
tags left to removed requirements or to criteria a MODIFIED block drops, and
a passing run of each of the build, typecheck and lint commands that is
configured. It SHALL NOT run the test command, and SHALL NOT require an
`@ac` test for every criterion: the tests meet the code in review. When none
of the build, typecheck and lint commands is configured, the gate SHALL pass
that check with a warning saying so and that the tests run in review.

#### Scenario: AC-FLOW-008.1 Everything done

- **WHEN** every `[code]` task is ticked, every requirement has `@req` code and the configured build, typecheck and lint commands pass
- **THEN** the gate passes and shows each command it ran

#### Scenario: AC-FLOW-008.2 What is missing

- **WHEN** a requirement has no `@req` code and `[code]` tasks are open
- **THEN** the gate fails listing the requirement and the open `[code]` tasks; open `[test]` tasks are not listed

#### Scenario: AC-FLOW-008.3 A failing build, typecheck or lint

- **WHEN** the configured build, typecheck or lint command fails (even with output that is not text)
- **THEN** the gate fails with that command's output

#### Scenario: AC-FLOW-008.4 No build, typecheck or lint command

- **WHEN** none of the build, typecheck and lint commands is configured
- **THEN** the gate passes with the warning `no build, typecheck or lint command configured: the tests run in review`

#### Scenario: AC-FLOW-008.5 Removed and dropped

- **WHEN** code or tests are still tagged with a removed requirement, its criteria, or a criterion a MODIFIED block drops
- **THEN** the code gate fails listing them (the test gate only warns), and passes once they are gone

#### Scenario: AC-FLOW-008.6 Criteria without tests

- **WHEN** some criteria have no `@ac` test and everything else passes
- **THEN** the code gate passes

#### Scenario: AC-FLOW-008.9 The tests are not run

- **GIVEN** a configured test command that fails, or no test command at all
- **WHEN** the code gate runs and everything else passes
- **THEN** it passes, and its result names no test command

#### Scenario: AC-FLOW-008.10 Only the configured commands

- **GIVEN** a project that configures only a typecheck command
- **WHEN** the code gate runs
- **THEN** it runs the typecheck command alone and shows no build or lint check
