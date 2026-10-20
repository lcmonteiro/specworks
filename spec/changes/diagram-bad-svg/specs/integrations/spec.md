# Spec Delta: integrations

## MODIFIED Requirements

### Requirement: REQ-INTEG-003 The d2 that renders

The system SHALL render with the d2 that pyd2 provides (its pinned release),
or with the program named by `SPECWORKS_D2` when that is set. A missing d2, a d2
that doesn't run, a d2 compile error, and an SVG that d2 wrote but that can't be
read or stamped SHALL each be reported as an error naming the diagram, never as
a crash.

#### Scenario: AC-INTEG-003.1 Which d2

- **WHEN** `SPECWORKS_D2` is set, or not
- **THEN** it is used, or pyd2's d2 is, whose `--version` is pyd2's pinned release

#### Scenario: AC-INTEG-003.2 No d2, or one that doesn't run

- **WHEN** pyd2 has no binary, or `SPECWORKS_D2` names a program that doesn't run
- **THEN** rendering fails with `cannot render <name>.d2: …`, and the d2 is reported as missing when there is none

#### Scenario: AC-INTEG-003.3 A d2 error

- **WHEN** d2 fails to compile a source
- **THEN** the error d2 printed is reported for that diagram

#### Scenario: AC-INTEG-003.4 An SVG that can't be stamped

- **WHEN** d2 succeeds but writes an SVG whose `<?xml` declaration never closes, writes no SVG, or writes one that isn't UTF-8
- **THEN** that diagram fails with `cannot render <name>.d2: …`, the other diagrams of the run still render, and the command exits 1
