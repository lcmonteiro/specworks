# Spec Delta: specs

## ADDED Requirements

### Requirement: REQ-SPECS-018 The trace of a closed change

`trace` SHALL give the matrix of an archived change as REQ-SPECS-012 gives an
active one's: from its delta specs and tasks, and the `@ac` and `@req` tags of
the current code. It SHALL mark each test and code location whose file
changed since the change was closed (the commit that archived it), and SHALL
say, without marking anything, when that cannot be told (no git, or no such
commit). The criteria it reports as removed but still tagged SHALL be those
the change's MODIFIED and REMOVED blocks leave out of the living spec as it
was at that commit, so a criterion a later change added is never reported;
when that commit cannot be found, no criterion SHALL be reported as removed.

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

#### Scenario: AC-SPECS-018.4 A criterion added after the close

- **GIVEN** a closed change whose MODIFIED REQ-X-001 has AC-X-001.1 and leaves out AC-X-001.2 (tagged in a test), and a later commit that adds AC-X-001.3 to the living spec and tags a test with it
- **WHEN** its trace is read
- **THEN** AC-X-001.3 is not reported as removed, and AC-X-001.2 still is

#### Scenario: AC-SPECS-018.5 No close commit

- **GIVEN** a closed change whose MODIFIED block leaves out a criterion still tagged in a test
- **WHEN** its trace is read outside a git repository
- **THEN** no criterion is reported as removed
