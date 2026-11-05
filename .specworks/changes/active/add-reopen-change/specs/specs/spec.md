## ADDED Requirements

### Requirement: REQ-SPECS-017 A change's own IDs from an earlier close

A requirement ID SHALL be a change's own when a History line of the
capability's requirements.md names the change (by the ref close wrote, `name` or
`module:name`) and lists the ID as ADDED, MODIFIED or REMOVED: the change merged
it at an earlier close and has been reopened. For its own IDs, `check` SHALL
accept an ADDED ID the living spec already has and a REMOVED ID it no longer
has, and SHALL NOT warn that the change's own earlier close MODIFIED a
requirement after the change started. The merge SHALL replace the block of an
own ADDED ID in place and list it as MODIFIED in the History line, and SHALL
skip an own REMOVED ID the living spec no longer has, leaving it out of the
line. An ID that is not the change's own SHALL keep the errors of REQ-SPECS-006
and REQ-SPECS-013, and an own ADDED ID the living spec no longer has and History
shows removed SHALL still be refused as retired.

#### Scenario: AC-SPECS-017.1 An own ADDED ID in the living spec

- **GIVEN** a living spec with REQ-X-005, a History line `add-x: ADDED REQ-X-005`, and a delta of `add-x` that ADDs REQ-X-005
- **WHEN** `check` runs
- **THEN** it reports no error for REQ-X-005

#### Scenario: AC-SPECS-017.2 An own REMOVED ID already gone

- **GIVEN** a History line `add-x: REMOVED REQ-X-003`, a living spec without REQ-X-003, and a delta of `add-x` that REMOVEs it with its Reason and Migration
- **WHEN** `check` runs
- **THEN** it reports no error for REQ-X-003

#### Scenario: AC-SPECS-017.3 Another change's ID

- **GIVEN** a living spec with REQ-X-005, a History line `other: ADDED REQ-X-005`, and a delta of `add-x` that ADDs REQ-X-005 or REMOVEs a REQ-X-003 that no History line shows `add-x` removed
- **WHEN** `check` runs
- **THEN** it fails as before: the ID already exists, or is not in the living spec

#### Scenario: AC-SPECS-017.4 The change's own earlier close

- **GIVEN** a change `add-x` created before its own History line `add-x: MODIFIED REQ-X-002`, and a delta of `add-x` that MODIFIEs REQ-X-002
- **WHEN** `check` runs
- **THEN** it does not warn that REQ-X-002 was MODIFIED after the change started; a line of another change at the same time still warns

#### Scenario: AC-SPECS-017.5 Replaced in place at the second close

- **GIVEN** a living spec with REQ-X-004, REQ-X-005 (as the first close left it) and REQ-X-006, a History line `add-x: ADDED REQ-X-005`, and a delta of `add-x` that ADDs a reworded REQ-X-005
- **WHEN** the change closes again
- **THEN** the living REQ-X-005 holds the reworded text between REQ-X-004 and REQ-X-006, and a second History line `add-x: MODIFIED REQ-X-005` follows the first, which is kept

#### Scenario: AC-SPECS-017.6 An own REMOVED ID already gone at the second close

- **GIVEN** a History line `add-x: REMOVED REQ-X-003`, a living spec without REQ-X-003, and a delta of `add-x` that REMOVEs it
- **WHEN** the change closes again
- **THEN** the close succeeds and the new History line does not list REQ-X-003

#### Scenario: AC-SPECS-017.7 Another change's ID at close

- **GIVEN** a living spec with REQ-X-005 that a History line attributes to `other`, and a delta of `add-x` that ADDs REQ-X-005
- **WHEN** the change closes
- **THEN** the close stops saying it is already in the living spec, and writes nothing

#### Scenario: AC-SPECS-017.8 An own ID removed since

- **GIVEN** History lines `add-x: ADDED REQ-X-005` and `other: REMOVED REQ-X-005`, a living spec without REQ-X-005, and a delta of `add-x` that ADDs it
- **WHEN** `check` runs
- **THEN** it fails saying the ID was removed and IDs are never reused

## MODIFIED Requirements

### Requirement: REQ-SPECS-006 A delta against its living spec

`check` SHALL refuse an ADDED ID that the living spec has or its History shows
was removed, and a MODIFIED or REMOVED ID the living spec doesn't have, except
for the IDs a change merged at an earlier close (REQ-SPECS-017). A
REMOVED requirement SHALL need a `Reason` and a `Migration` line, each with
text. A capability with no living spec SHALL take only ADDED requirements and
be warned to have a Purpose; one not registered SHALL be warned to be
registered, and SHALL be refused a prefix another capability uses. `check`
SHALL warn about a MODIFIED block that leaves out a living criterion, one that
another change MODIFIED after this one started (by the close time a History
line holds, or by its day when it holds only a day), and a living spec it would
refuse to merge into.

#### Scenario: AC-SPECS-006.1 IDs that don't match the living spec

- **WHEN** an ADDED ID is already in the living spec, or a MODIFIED one is not, and the change did not merge it at an earlier close
- **THEN** `check` fails, saying to use MODIFIED or that the ID is not in the living spec

#### Scenario: AC-SPECS-006.2 A removed ID

- **WHEN** a change ADDs an ID that the History of requirements.md shows was removed
- **THEN** `check` fails saying IDs are never reused

#### Scenario: AC-SPECS-006.3 Removing a requirement

- **WHEN** a REMOVED requirement lacks a `Reason` or a `Migration` line with text (bold or a bullet allowed)
- **THEN** `check` fails naming the missing line

#### Scenario: AC-SPECS-006.4 A new capability

- **WHEN** a delta spec is for a capability with no living spec, or not registered
- **THEN** MODIFIED and REMOVED are errors, a missing Purpose and the missing registration are warnings, and a prefix in use is an error

#### Scenario: AC-SPECS-006.5 A MODIFIED block out of date

- **WHEN** a MODIFIED block leaves out a living criterion, or another change MODIFIED the requirement after this one started
- **THEN** `check` warns, naming the criterion or the other change

#### Scenario: AC-SPECS-006.6 A broken living spec

- **WHEN** the living spec of a delta's capability is broken
- **THEN** `check` warns to fix it before closing

#### Scenario: AC-SPECS-006.7 Closed earlier the same day

- **GIVEN** a change that started at 23:00 MODIFIES a requirement, and a History line of that day, timed 22:41:07, says another change MODIFIED it
- **WHEN** `check` runs
- **THEN** it doesn't warn; with a line timed after 23:00, or one holding only that day, it warns

### Requirement: REQ-SPECS-013 Merging at close

Closing SHALL merge each delta into its capability's living spec as text:
ADDED blocks at the end of `## Requirements`, MODIFIED blocks in place, REMOVED
blocks deleted, everything else kept as written; the blocks of a change's own
IDs from an earlier close are merged as REQ-SPECS-017 says. A capability without a living
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

- **WHEN** a MODIFIED or REMOVED ID is not in the living spec, an ADDED one is, or the living spec is broken, and the change did not merge the ID at an earlier close
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
