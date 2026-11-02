## MODIFIED Requirements

### Requirement: REQ-SPECS-016 Finding living requirements by term

The system SHALL list every requirement in the living specs of the
workspace's capabilities, in every module, whose title, text or scenarios
contain at least one of the given terms, compared literally and ignoring
case. The spec's markup SHALL not count: the `Requirement:` and
`Scenario:` keywords of the headings and the bold `GIVEN`, `WHEN`, `THEN` and
`AND` of the steps; the rest of those lines (IDs, titles, steps) SHALL. A term
that matches more than half of the living requirements searched SHALL be
reported as broad, with how many of them it matched; its matches SHALL still
be listed. Each match SHALL name the capability's ref, the requirement's ID and
title, and the first matching line with its living spec's path and line
number, in capability order then requirement order. A capability without a
living spec SHALL be skipped. An empty term SHALL be refused.

#### Scenario: AC-SPECS-016.1 A term in a requirement's text

- **GIVEN** a living requirement REQ-AUTH-002 whose text mentions `--no-branch`
- **WHEN** the requirements are searched for `--NO-BRANCH`
- **THEN** REQ-AUTH-002 is listed with its capability, title, and the line that holds `--no-branch` with its number

#### Scenario: AC-SPECS-016.2 A term in a scenario

- **GIVEN** a requirement whose term appears only in one of its scenarios
- **WHEN** the requirements are searched for that term
- **THEN** it is listed, and its matching line is the scenario's line

#### Scenario: AC-SPECS-016.3 Several terms

- **WHEN** the requirements are searched for two terms, each found in a different requirement
- **THEN** both requirements are listed, each once

#### Scenario: AC-SPECS-016.4 A capability of a module

- **GIVEN** module `billing` with a capability whose living requirement mentions the term
- **WHEN** the requirements are searched from the top level
- **THEN** that requirement is listed under `billing:<capability>`

#### Scenario: AC-SPECS-016.5 No match

- **WHEN** no living requirement contains the term
- **THEN** the result is empty

#### Scenario: AC-SPECS-016.6 An empty term

- **WHEN** the requirements are searched for an empty or blank term
- **THEN** it is refused, naming the term

#### Scenario: AC-SPECS-016.7 The markup does not match

- **GIVEN** living requirements whose words never say "requirement", "scenario" or "when", and REQ-AUTH-002 whose text says "when the link expires"
- **WHEN** the requirements are searched for `requirement`, then `scenario`, then `when`
- **THEN** the first two find nothing, and `when` finds only REQ-AUTH-002, at its text's line; searching for `REQ-AUTH-002` or a scenario's title still finds it

#### Scenario: AC-SPECS-016.8 A broad term

- **GIVEN** three living requirements, two of which mention `token` and one `expired`
- **WHEN** the requirements are searched for `token` and `expired`
- **THEN** all three are listed, `token` is reported as broad with 2 of 3, and `expired` (1 of 3) is not
