# Spec Delta: specs

## ADDED Requirements

### Requirement: REQ-SPECS-018 The trace of a closed change

`trace` SHALL give the matrix of an archived change as REQ-SPECS-012 gives an
active one's: from its delta specs and tasks, and the `@ac` and `@req` tags of
the current code. It SHALL mark each test and code location whose file
changed since the change was closed (the commit that archived it), and SHALL
say, without marking anything, when that cannot be told (no git, or no such
commit).

#### Scenario: AC-SPECS-018.1 A closed change

- **GIVEN** a closed change whose criteria have tests and code
- **WHEN** its trace is read
- **THEN** each criterion is linked to its current tests and its requirement's code, as for an active change

#### Scenario: AC-SPECS-018.2 Changed since the close

- **GIVEN** a closed change, and a later commit that changes one of its code files
- **WHEN** its trace is read
- **THEN** the locations in that file are marked as changed since the close, and the others are not

#### Scenario: AC-SPECS-018.3 Without git

- **WHEN** the trace of a closed change is read outside a git repository
- **THEN** no location is marked, and the trace says it cannot tell what changed since the close
