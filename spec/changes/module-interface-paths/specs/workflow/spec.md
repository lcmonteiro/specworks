# Spec Delta: workflow

## MODIFIED Requirements

### Requirement: REQ-FLOW-006 Gate design

The design gate SHALL require an Interfaces section in design.md (found by its
heading in any case, HTML comments and code fences ignored), with every file
named in its code spans existing inside the change's module folder, written
relative to that folder or to the workspace root. `None` SHALL pass without files, and prose
naming no file SHALL be a warning. It SHALL run the build and typecheck commands
when they are configured. The existing test suite must pass, except once the
change already has `@ac` tests, when a red suite is only a warning.

#### Scenario: AC-FLOW-006.1 The Interfaces section

- **WHEN** design.md has no Interfaces heading, or only a template comment under it
- **THEN** the gate fails on the Interfaces check; a heading like `## Interfaces (API)` or `## interfaces` counts

#### Scenario: AC-FLOW-006.2 Named files exist

- **WHEN** the Interfaces section names files in code spans (`src/auth/reset.py:ResetService`)
- **THEN** the gate fails listing those that do not exist, and passes once they do; names without a folder count only with a code extension

#### Scenario: AC-FLOW-006.3 None and prose

- **WHEN** the section says `None`, or describes the API without any file
- **THEN** the gate passes; prose without files is a non-blocking warning

#### Scenario: AC-FLOW-006.4 The existing tests

- **WHEN** the test suite fails and the change has no `@ac` tests of its own
- **THEN** the gate fails; once the change has `@ac` tests, the failure is a warning saying so

#### Scenario: AC-FLOW-006.5 Build and typecheck

- **WHEN** `build` and `typecheck` are configured
- **THEN** they run as checks of their own, and none are shown when they are not configured

#### Scenario: AC-FLOW-006.6 A file outside the change's module

- **GIVEN** a change in module `billing` (at `services/billing`) whose Interfaces name `src/invoices.py`, and a `src/invoices.py` that exists only at the workspace root
- **WHEN** the design gate runs
- **THEN** it fails listing `src/invoices.py`; it passes once the file exists in the module, named either `src/invoices.py` or `services/billing/src/invoices.py`
