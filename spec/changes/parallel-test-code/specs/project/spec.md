## MODIFIED Requirements

### Requirement: REQ-PROJ-011 Change phases

The system SHALL track a change through the phases refine, specify, design,
implement, review, validate, close and done, letting a change move to any of
them except `done`, which only closing reaches. `test` and `code` SHALL NOT be
phases: a change whose metadata names `test` or `code` (saved before
`implement` existed) SHALL be read as being in `implement`, and moving a change
to `test` or `code` SHALL be refused, naming `implement`. A change whose
metadata cannot be read SHALL be an error naming its file.

#### Scenario: AC-PROJ-011.1 Moving between phases

- **WHEN** a change is moved to a phase, forward or back
- **THEN** its phase is that one, and the phases are listed in workflow order

#### Scenario: AC-PROJ-011.2 Done only through close

- **WHEN** a change is moved to `done` directly
- **THEN** it is refused, saying only close makes a change done

#### Scenario: AC-PROJ-011.3 Broken metadata

- **WHEN** a change's `.change.yaml` is not a mapping, is not YAML, or names an unknown phase
- **THEN** reading the change fails with an error naming the file and the problem

#### Scenario: AC-PROJ-011.4 A change saved in test or code

- **GIVEN** a change whose `.change.yaml` says `phase: test` (or `phase: code`)
- **WHEN** the change is read
- **THEN** its phase is `implement`

#### Scenario: AC-PROJ-011.5 Test and code are not phases

- **WHEN** a change is moved to `test` or `code`
- **THEN** it is refused, naming `implement`, and its phase is unchanged
