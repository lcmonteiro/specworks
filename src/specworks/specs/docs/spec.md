# specs

## Purpose

Specs and traceability: spec files, capabilities, format checks, tasks, the
trace matrix that links requirements to tasks, tests and code through `@ac` /
`@req` tags, and merging deltas into living specs at close.

## Requirements

### Requirement: REQ-SPECS-001 Ignore the tags on one line

The tag scan SHALL skip every tag on a line that holds the marker
`specworks: ignore-tags` (not followed by `-`), wherever the marker is on the
line and whatever comment syntax surrounds it. Tags on other lines of the same
file SHALL still be found.

#### Scenario: AC-SPECS-001.1 A marked line

- **GIVEN** a test file with a tag on a line that ends with `# specworks: ignore-tags`, and a tag on the next line with no marker
- **WHEN** the tags are scanned
- **THEN** only the tag on the unmarked line is found

#### Scenario: AC-SPECS-001.2 Any comment syntax

- **GIVEN** a source file whose line holds a tag and `// specworks: ignore-tags`
- **WHEN** the tags are scanned
- **THEN** no tag is found on that line

### Requirement: REQ-SPECS-002 Ignore the tags in a block of lines

The tag scan SHALL skip every tag on the lines from a
`specworks: ignore-tags-start` marker to the next `specworks: ignore-tags-end`
marker in the same file, both included. A start with no end SHALL run to the end of
that file. A start or end marker SHALL count only on a line with no other letters
or digits (comment punctuation only). An end with no open block SHALL be ignored.

#### Scenario: AC-SPECS-002.1 A block

- **GIVEN** a file with tags before, inside and after a block of `# specworks: ignore-tags-start` … `# specworks: ignore-tags-end`
- **WHEN** the tags are scanned
- **THEN** the tags before and after the block are found and the ones inside are not

#### Scenario: AC-SPECS-002.2 A start with no end

- **GIVEN** a file with a start marker and no end marker, and another file with tags
- **WHEN** the tags are scanned
- **THEN** no tag after the start is found in that file, and the other file's tags are found

#### Scenario: AC-SPECS-002.3 A marker quoted in prose

- **GIVEN** a line that quotes the start marker among other words (e.g. `Lines from specworks: ignore-tags-start are skipped`), followed by a tag
- **WHEN** the tags are scanned
- **THEN** the tag is found: the quoted marker does not open a block

#### Scenario: AC-SPECS-002.4 An end with no start

- **GIVEN** a file with an end marker and no start marker, then a tag
- **WHEN** the tags are scanned
- **THEN** the tag is found

### Requirement: REQ-SPECS-003 Ignored tags are left out of every check

The system SHALL treat an ignored tag as if it were not there: it SHALL count
neither as a test or code for a requirement or criterion, nor as an unknown
tag.

#### Scenario: AC-SPECS-003.1 Not an unknown tag

- **GIVEN** an ignored tag with a prefix no capability uses
- **WHEN** a change is traced
- **THEN** it is not listed as an unknown tag

#### Scenario: AC-SPECS-003.2 Not coverage

- **GIVEN** a criterion of the change whose only `@ac` tag is ignored
- **WHEN** a change is traced
- **THEN** the criterion is listed as having no test

### Requirement: REQ-SPECS-004 Reading spec files

The system SHALL read a spec file into its Purpose, its `## ` sections and the
`### Requirement:` blocks of each, every block with its ID, title, description
and `#### Scenario:` criteria. A requirement ID SHALL be `REQ-<prefix>-<n>` and
a criterion ID `AC-<prefix>-<n>.<m>`, the number being the last segment, so a
prefix may hold several segments, all-digit ones included. Headings inside code
fences or HTML comments SHALL be text. A living spec SHALL be reported as
broken when a block is outside `## Requirements`, lacks an ID, SHALL/MUST or a
criterion, repeats an ID, or holds a criterion numbered under another
requirement.

#### Scenario: AC-SPECS-004.1 A living spec

- **WHEN** a living spec with a Purpose and requirements is read
- **THEN** each requirement has its ID, title, description and criteria, and writing a block back gives the same text

#### Scenario: AC-SPECS-004.2 Examples are text

- **WHEN** a requirement holds a heading inside a code fence (``` or ~~~) or an HTML comment
- **THEN** it is part of the requirement's text, not a new block

#### Scenario: AC-SPECS-004.3 A prefix with an all-digit segment

- **WHEN** an ID such as `REQ-OAUTH-2-001` is read
- **THEN** its prefix is `OAUTH-2` and its number `001`

#### Scenario: AC-SPECS-004.4 A broken living spec

- **WHEN** a living spec has a requirement without an ID, SHALL/MUST or a criterion, an ID used twice, or a criterion under the wrong requirement
- **THEN** each problem is reported with its line

### Requirement: REQ-SPECS-005 Format of a delta spec

`check` SHALL report as an error a delta spec with no ADDED, MODIFIED or
REMOVED requirement, a `## Requirements` section, or a requirement or criterion
that lacks its ID, uses another capability's prefix, has no title, repeats an ID
in the change, states nothing with SHALL or MUST, has no criterion, numbers a
criterion under another requirement, writes a scenario header without exactly
four hashes, or has no WHEN and THEN. A description longer than 1000 characters
SHALL be a warning.

#### Scenario: AC-SPECS-005.1 Format errors

- **WHEN** a requirement or criterion breaks one of these rules
- **THEN** `check` fails with an error naming the rule and the line

#### Scenario: AC-SPECS-005.2 An ID used twice

- **WHEN** two delta specs of a change use the same requirement ID
- **THEN** `check` fails with `is used twice`, naming the other place

#### Scenario: AC-SPECS-005.3 Nothing to check

- **WHEN** a delta spec has no requirements, or a requirement has no scenario
- **THEN** `check` fails saying what to add

#### Scenario: AC-SPECS-005.4 A long description

- **WHEN** a requirement's description is longer than 1000 characters
- **THEN** `check` warns, without failing, to keep one behaviour per requirement

### Requirement: REQ-SPECS-006 A delta against its living spec

`check` SHALL refuse an ADDED ID that the living spec has or its History shows
was removed, and a MODIFIED or REMOVED ID the living spec doesn't have. A
REMOVED requirement SHALL need a `Reason` and a `Migration` line, each with
text. A capability with no living spec SHALL take only ADDED requirements and
be warned to have a Purpose; one not registered SHALL be warned to be
registered, and SHALL be refused a prefix another capability uses. `check`
SHALL warn about a MODIFIED block that leaves out a living criterion, one that
another change MODIFIED after this one started (by the close time a History
line holds, or by its day when it holds only a day), and a living spec it would
refuse to merge into.

#### Scenario: AC-SPECS-006.1 IDs that don't match the living spec

- **WHEN** an ADDED ID is already in the living spec, or a MODIFIED one is not
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

### Requirement: REQ-SPECS-007 Two active changes on one requirement

When two active changes ADD the same ID, or MODIFY or REMOVE the same
requirement, `check` SHALL fail only the change that started later (by its start
time, then by name), and only warn the one that started first, so they never
block each other.

#### Scenario: AC-SPECS-007.1 The same ID added twice

- **WHEN** two active changes ADD the same requirement ID
- **THEN** the later one fails `check` and the earlier one gets a warning

#### Scenario: AC-SPECS-007.2 One requirement edited twice

- **WHEN** two active changes MODIFY the same requirement
- **THEN** the later one fails saying to close the other first, and the earlier one gets a warning

### Requirement: REQ-SPECS-008 The proposal and the delta specs

`check` SHALL require `proposal.md` with `## Why`, `## What Changes` and
`## Capabilities` (headings in code fences don't count), and at least one delta
spec at `specs/[<module>/]<capability>/spec.md`, unless the change is marked
`skip-specs`, which SHALL then have none. A delta spec under a folder that is
not a module SHALL be an error naming the expected paths.

#### Scenario: AC-SPECS-008.1 A complete plan

- **WHEN** a change has its proposal, delta specs and tasks, all well formed
- **THEN** `check` passes

#### Scenario: AC-SPECS-008.2 Missing pieces

- **WHEN** the proposal or its sections are missing (or only inside a code fence), or there is no delta spec
- **THEN** `check` fails naming what to write, and offers `skip-specs` for a change with no behaviour change

#### Scenario: AC-SPECS-008.3 skip-specs

- **WHEN** a change marked `skip-specs` has no delta specs, or has some
- **THEN** `check` passes, or fails with `skip_specs is set but the change has delta specs`

#### Scenario: AC-SPECS-008.4 An unknown module

- **WHEN** a delta spec is at `specs/<folder>/<capability>/spec.md` and `<folder>` is not a module
- **THEN** `check` fails saying it is not a module

### Requirement: REQ-SPECS-009 Tasks

Tasks SHALL be the `- [ ] N.M text` lines of tasks.md (`- [x]` when done); lines
in code fences and after `## Workflow follow-up` SHALL not be tasks. `check`
SHALL report a task-like line in another format, a number used twice, a task
naming an ID the change's specs don't have, and an ADDED or MODIFIED criterion
no task names (by its ID or its requirement's); a missing tasks.md SHALL be a
warning and one with no task an error. Ticking or unticking a task SHALL change
only its checkbox, and SHALL refuse an unknown number.

#### Scenario: AC-SPECS-009.1 Task format and IDs

- **WHEN** tasks.md has a malformed task or a task naming an unknown ID
- **THEN** `check` fails naming the line

#### Scenario: AC-SPECS-009.2 Every criterion has a task

- **WHEN** a criterion of the change is named by no task, nor is its requirement
- **THEN** `check` fails naming the criterion

#### Scenario: AC-SPECS-009.3 Not tasks

- **WHEN** tasks.md shows a task inside a code fence, or lists bullets under `## Workflow follow-up`
- **THEN** they are not tasks

#### Scenario: AC-SPECS-009.4 No tasks yet

- **WHEN** tasks.md is missing, or has no task
- **THEN** `check` warns, or fails asking for `- [ ] 1.1` checkboxes

#### Scenario: AC-SPECS-009.5 Ticking a task

- **WHEN** `task done` and `task undo` run on a task, or on an unknown number
- **THEN** only that task's checkbox changes, or the unknown number is refused listing the tasks

### Requirement: REQ-SPECS-010 Finding a capability and its next ID

A bare capability name SHALL mean the current module's capability, else the
only module that has it; a name several modules have SHALL be an error listing
their `module:name` refs; a name no module has SHALL be a new capability of the
current module, with a prefix derived from its name. The next free requirement
ID SHALL be one more than the highest number in the living spec, its History
(removed requirements too) and every active change's delta spec.

#### Scenario: AC-SPECS-010.1 Describing a capability

- **WHEN** `spec show` names an existing capability, one of a module, or a new one
- **THEN** it shows its prefix, delta path, living spec and requirements, the module's own path and prefix, or a derived prefix for the new one

#### Scenario: AC-SPECS-010.2 The next ID

- **WHEN** an active change adds a requirement, or a close removed the highest one
- **THEN** the next ID is past both

#### Scenario: AC-SPECS-010.3 A name in several modules

- **WHEN** a bare capability name is in two modules and in neither the current one
- **THEN** it fails listing both `module:name` refs

### Requirement: REQ-SPECS-011 Finding the tags

The tag scan SHALL find every `@req` and `@ac` tag in the workspace's files,
several IDs per tag allowed, each file read with the globs of the innermost
module holding it. A file SHALL be a test when it matches `test_globs` or, with
none set, when its name or folder looks like a test. Tests SHALL always be
scanned; `source_globs`, when set, SHALL limit the other files; otherwise
documentation SHALL not be scanned. Hidden, vendored and workflow folders SHALL
be skipped, and so SHALL files over 1 MB or not in UTF-8. In globs, `*` and `?`
SHALL stay within a folder and `**` SHALL span folders.

#### Scenario: AC-SPECS-011.1 Tests and code

- **WHEN** a test and a source file carry tags, one listing several IDs
- **THEN** each ID is found, as a test or as code

#### Scenario: AC-SPECS-011.2 What is a test

- **WHEN** files are named like `test_x.py`, `x_test.go`, `x.spec.ts` or sit in `tests/`, or `test_globs` is set
- **THEN** those are tests, and with `test_globs` set only the files they match

#### Scenario: AC-SPECS-011.3 Documentation and source_globs

- **WHEN** a README quotes a tag, a glob names a doc file, or `source_globs` is set
- **THEN** the README's tag is not found, the named doc is scanned, and other files outside `source_globs` are skipped but tests are not

#### Scenario: AC-SPECS-011.4 Skipped folders

- **WHEN** tags are in the workflow folder or a hidden folder
- **THEN** they are not found

#### Scenario: AC-SPECS-011.5 Globs

- **WHEN** paths are matched against `*`, `?` and `**` globs
- **THEN** `*` and `?` stay within one folder and `**` spans any number of folders, none included

#### Scenario: AC-SPECS-011.6 Files not read

- **WHEN** a file is over 1 MB or not UTF-8
- **THEN** its tags are not found, and the scan goes on

### Requirement: REQ-SPECS-012 The trace matrix

`trace` SHALL list, for each criterion of the change, its requirement, the
tasks that name it or its requirement, its tests (`@ac`) and its requirement's
code (`@req`), and SHALL report the gaps: criteria without a task or a test,
requirements without code, and removed requirements or criteria still tagged.
A tag SHALL be unknown when its ID belongs to one of the change's capabilities
but no spec has it, when its prefix no capability uses (suggesting a close one),
or when it is not an ID; IDs in other active changes' delta specs SHALL be
known. `trace --write` SHALL write the matrix to traceability.md.

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

### Requirement: REQ-SPECS-013 Merging at close

Closing SHALL merge each delta into its capability's living spec as text:
ADDED blocks at the end of `## Requirements`, MODIFIED blocks in place, REMOVED
blocks deleted, everything else kept as written. A capability without a living
spec SHALL get one with the delta's Purpose. requirements.md SHALL be rewritten
as an index of the requirements and criteria plus its `## History`, one line
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

### Requirement: REQ-SPECS-014 Diagrams of a change

`check` SHALL report an image design.md shows that doesn't exist as an error,
and warn about a diagram with no SVG or an outdated one, and one design.md
doesn't show.

#### Scenario: AC-SPECS-014.1 Diagram problems

- **WHEN** design.md shows a missing image, a diagram has no SVG, and another isn't shown in design.md
- **THEN** `check` reports the missing image as an error and the other two as warnings
