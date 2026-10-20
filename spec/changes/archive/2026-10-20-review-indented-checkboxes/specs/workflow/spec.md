# Spec Delta: workflow

## MODIFIED Requirements

### Requirement: REQ-FLOW-010 Reading review.md

The system SHALL read each finding in review.md as a checkbox with its ID
(`- [ ] R<n>`, also `*`, `1.` and a bold ID), open or done, with a type (the
first bold word that is a known type, in any case). It SHALL route the finding
to the phase of its type, or to the phase of a `back to <phase>:` in its own
block, and after a `done in <phase>:` to the phase after that one. HTML comments
and code fences SHALL be ignored. A checkbox outside a finding's block (at the
top level or indented, ticked or not), and an open finding with no known type or
phase, SHALL be reported as unreadable.

#### Scenario: AC-FLOW-010.1 Finding variants

- **WHEN** a finding is written with `*`, a numbered bullet or a bold ID
- **THEN** it is read as finding R1

#### Scenario: AC-FLOW-010.2 Unreadable checkboxes

- **WHEN** review.md has a checkbox that is not `R<n> …`, or an open finding of unknown type with no `back to`
- **THEN** the review gate and validate fail on readability, even with `--allow-open`

#### Scenario: AC-FLOW-010.3 Types and routing

- **WHEN** a finding's bold type is in another case or after another bold word, or its block says `back to <phase>:`
- **THEN** it is routed to that type's or that `back to` phase; prose like "goes back to design" does not route it

#### Scenario: AC-FLOW-010.4 Code fences

- **WHEN** a finding appears in a code fence, or a fence or sub-checkbox sits under a finding
- **THEN** the fenced finding is an example, and the finding above the fence stays open and routed

#### Scenario: AC-FLOW-010.5 A checkbox indented outside any finding

- **GIVEN** review.md with `- Follow-ups:` followed by `  - [ ] reset still ignores case`, and no finding above it
- **WHEN** it is read
- **THEN** the checkbox is reported as unreadable, so the review gate fails (also with `--allow-open`); the same checkbox under a finding stays part of that finding
