## MODIFIED Requirements

### Requirement: REQ-FLOW-013 Validate

`specworks validate` SHALL run grouped checks (completeness, correctness,
coherence), each naming the phase skill that fixes a failure, and give a PASS
verdict when no blocking check fails. Open tasks SHALL be checked by kind,
each kind naming its own phase skill: `[test]` tasks the test skill, `[code]`
tasks the code skill, and tasks with neither marker the design skill. It SHALL
run the test command (lint and typecheck when configured) and check that
diagram SVGs are up to date. It SHALL write nothing. Not having gone through
review is a warning. `gate validate` SHALL apply the same checks.

#### Scenario: AC-FLOW-013.1 A finished change

- **WHEN** a reviewed change is validated
- **THEN** the verdict is PASS, every check has a group, and an unconfigured lint is reported as `not configured`

#### Scenario: AC-FLOW-013.2 Read-only

- **WHEN** validate and `gate validate` run
- **THEN** no file of the project changes

#### Scenario: AC-FLOW-013.3 Where to go back

- **WHEN** checks fail (an open task, untagged requirement, missing review.md)
- **THEN** the verdict is FAIL and each failure names its phase skill; `goBackTo` lists them

#### Scenario: AC-FLOW-013.4 Failing commands

- **WHEN** the test or lint command fails
- **THEN** the check is critical and shows the command's output

#### Scenario: AC-FLOW-013.5 Outdated diagram

- **WHEN** a change's diagram has no SVG or an outdated one
- **THEN** the coherence check fails naming the SVG

#### Scenario: AC-FLOW-013.6 Review skipped

- **WHEN** the change never reached review
- **THEN** a non-blocking warning names its phase

#### Scenario: AC-FLOW-013.7 gate validate

- **WHEN** `gate validate` runs
- **THEN** it passes and fails as validate does

#### Scenario: AC-FLOW-013.8 Open tasks by kind

- **WHEN** a `[test]` task, a `[code]` task and a task with no marker are open
- **THEN** each kind fails its own completeness check listing only its open tasks, naming `/specworks-test`, `/specworks-code` and `/specworks-design`; `goBackTo` lists all three
