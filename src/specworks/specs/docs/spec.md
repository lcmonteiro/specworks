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
