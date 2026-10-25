## MODIFIED Requirements

### Requirement: REQ-FLOW-006 Gate design

The design gate SHALL require an Interfaces section in design.md (found by its
heading in any case, HTML comments and code fences ignored), with every file
named in its code spans existing inside the change's module folder, written
relative to that folder or to the workspace root. `None` SHALL pass without files, and prose
naming no file SHALL be a warning. It SHALL run the build and typecheck commands
when they are configured. The existing test suite must pass, except once the
change has tests of its own, when a red suite is only a warning. A change's
own tests SHALL be its `@ac` tests, or the test files changed since the change
started (committed, uncommitted or untracked); without git none are changed.

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

- **WHEN** the test suite fails and the change has no tests of its own (no `@ac` tests and no changed test files)
- **THEN** the gate fails; once the change has `@ac` tests, the failure is a warning saying so

#### Scenario: AC-FLOW-006.5 Build and typecheck

- **WHEN** `build` and `typecheck` are configured
- **THEN** they run as checks of their own, and none are shown when they are not configured

#### Scenario: AC-FLOW-006.6 A file outside the change's module

- **GIVEN** a change in module `billing` (at `services/billing`) whose Interfaces name `src/invoices.py`, and a `src/invoices.py` that exists only at the workspace root
- **WHEN** the design gate runs
- **THEN** it fails listing `src/invoices.py`; it passes once the file exists in the module, named either `src/invoices.py` or `services/billing/src/invoices.py`

#### Scenario: AC-FLOW-006.7 Changed test files without tags

- **GIVEN** a change with no `@ac` tests of its own, in a git repository where a test file changed since the change started
- **WHEN** the test suite fails
- **THEN** the gate passes with a warning saying the change has changed test files; without git, or with no changed test file, it fails

### Requirement: REQ-FLOW-008 Gate code

The code gate SHALL check the code half of implement: it SHALL require every
`[code]` task done, `@req` code for every requirement, no unknown tags, no
tags left to removed requirements or to criteria a MODIFIED block drops, and
a configured test command whose run passes. It SHALL NOT require an `@ac`
test for every criterion. While the change has tests of its own (its `@ac`
tests, or test files changed since it started, as in the design gate), a
failing run SHALL be a warning instead of blocking: those tests meet the code
in review.

#### Scenario: AC-FLOW-008.1 Everything done

- **WHEN** every `[code]` task is ticked, every requirement has `@req` code and the tests pass
- **THEN** the gate passes and shows the command it ran

#### Scenario: AC-FLOW-008.2 What is missing

- **WHEN** a requirement has no `@req` code and `[code]` tasks are open
- **THEN** the gate fails listing the requirement and the open `[code]` tasks; open `[test]` tasks are not listed

#### Scenario: AC-FLOW-008.3 Failing tests

- **GIVEN** a change with no tests of its own (no `@ac` tests and no changed test files)
- **WHEN** the test command fails (even with output that is not text)
- **THEN** the gate fails with the command's output

#### Scenario: AC-FLOW-008.4 No test command

- **WHEN** no test command is configured
- **THEN** the gate fails with `no 'test' command configured`

#### Scenario: AC-FLOW-008.5 Removed and dropped

- **WHEN** code or tests are still tagged with a removed requirement, its criteria, or a criterion a MODIFIED block drops
- **THEN** the code gate fails listing them (the test gate only warns), and passes once they are gone

#### Scenario: AC-FLOW-008.6 Criteria without tests

- **WHEN** some criteria have no `@ac` test and everything else passes
- **THEN** the code gate passes

#### Scenario: AC-FLOW-008.7 The change's own tests fail

- **GIVEN** a change with `@ac` tests of its own
- **WHEN** the test command fails
- **THEN** the gate passes with a warning showing the command's output

#### Scenario: AC-FLOW-008.8 A skip-specs change whose halves disagree

- **GIVEN** a change marked skip-specs, in a git repository where a test file changed since the change started
- **WHEN** the test command fails
- **THEN** the gate passes with a warning saying the change has changed test files, so `start review` can move the change on
