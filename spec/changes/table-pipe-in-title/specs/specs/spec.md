# Spec Delta: specs

## MODIFIED Requirements

### Requirement: REQ-SPECS-012 The trace matrix

`trace` SHALL list, for each criterion of the change, its requirement, the
tasks that name it or its requirement, its tests (`@ac`) and its requirement's
code (`@req`), and SHALL report the gaps: criteria without a task or a test,
requirements without code, and removed requirements or criteria still tagged.
A tag SHALL be unknown when its ID belongs to one of the change's capabilities
but no spec has it, when its prefix no capability uses (suggesting a close one),
or when it is not an ID; IDs in other active changes' delta specs SHALL be
known. `trace --write` SHALL write the matrix to traceability.md, with any `|` in a
title escaped as `\|` so it stays in its cell.

#### Scenario: AC-SPECS-012.1 The matrix

- **WHEN** a change's criteria have tasks, tests and code
- **THEN** `trace` links each criterion to them and `--write` writes traceability.md

#### Scenario: AC-SPECS-012.2 Removed and still tagged

- **WHEN** a REMOVED requirement, or a criterion a MODIFIED block leaves out, is still tagged
- **THEN** it is reported as removed but still tagged

#### Scenario: AC-SPECS-012.3 Unknown tags

- **WHEN** a tag uses a prefix no capability uses
- **THEN** it is unknown, with a suggestion when a prefix is close

#### Scenario: AC-SPECS-012.4 Tags that are not unknown

- **WHEN** a tag belongs to a capability whose prefix extends another's, or to another active change's delta (even a broken one)
- **THEN** it is not unknown, and the other change's broken delta doesn't break this trace

#### Scenario: AC-SPECS-012.5 A pipe in a title

- **WHEN** a requirement or criterion title holds `|` and `trace --write` runs
- **THEN** traceability.md shows it as `\|`, and its row has as many cells as the header

### Requirement: REQ-SPECS-013 Merging at close

Closing SHALL merge each delta into its capability's living spec as text:
ADDED blocks at the end of `## Requirements`, MODIFIED blocks in place, REMOVED
blocks deleted, everything else kept as written. A capability without a living
spec SHALL get one with the delta's Purpose. requirements.md SHALL be rewritten
as an index of the requirements and criteria (a `|` in a title escaped as
`\|`) plus its `## History`, one line
added per close with the close's local date and time. A delta that doesn't apply, a broken living spec or an
unregistered capability SHALL stop the close. Every file SHALL be computed
first, the archive folder checked, and the living docs restored if writing or
archiving fails.

#### Scenario: AC-SPECS-013.1 Merge and archive

- **WHEN** a change closes
- **THEN** its blocks are added, replaced or removed in the living spec, requirements.md gains the index and a History line, and the change moves to the archive marked done

#### Scenario: AC-SPECS-013.2 Everything else kept

- **WHEN** a living spec has other sections, headings after the last requirement, code fences or uneven blank lines
- **THEN** they are kept, and blank lines are tidied only where a block is spliced in

#### Scenario: AC-SPECS-013.3 A delta that doesn't apply

- **WHEN** a MODIFIED or REMOVED ID is not in the living spec, an ADDED one is, or the living spec is broken
- **THEN** the close stops with that error and writes nothing

#### Scenario: AC-SPECS-013.4 All or nothing

- **WHEN** the archive folder is taken, or archiving fails
- **THEN** nothing is written, or the living docs are put back as they were

#### Scenario: AC-SPECS-013.5 The close time in History

- **WHEN** a change closes
- **THEN** its History line holds the date and the time before the change's name (`- 2026-10-21 09:14:02 ...`), and the earlier lines are kept as they were

#### Scenario: AC-SPECS-013.6 A pipe in a title

- **WHEN** a change closes with a requirement titled `Read | write`
- **THEN** its requirements.md row reads `| REQ-… | Read \| write | … |`, three cells as in the header, and spec.md keeps the title as written
