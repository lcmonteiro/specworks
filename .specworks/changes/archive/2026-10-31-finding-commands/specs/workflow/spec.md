# Spec Delta: workflow

## ADDED Requirements

### Requirement: REQ-FLOW-016 Writing findings to review.md

The system SHALL write a change's review findings as review.md text that
REQ-FLOW-010 reads back: a new finding under `## Findings` with the next free
ID, its type and its Proposal (creating review.md from its template when
missing); a finding's Decision, replacing the one it has, which SHALL start
with `back to <step>:` or `accepted:` and, when `accepted`, tick the finding;
a `done in <step>:` line; and a tick with what review confirmed. It SHALL add
each line at the end of the finding's block and leave every other line of
the file as it was. It SHALL refuse an unknown finding, type or step, an
empty text, and a decision in another form, and SHALL write nothing when the
edited text does not read back with the expected finding.

#### Scenario: AC-FLOW-016.1 A new finding

- **GIVEN** a review.md with findings R1 and R2
- **WHEN** a `test-gap` finding is added with its text and proposal
- **THEN** it is R3, open, routed to the test half, with its Proposal line, and the lines of R1 and R2 are unchanged

#### Scenario: AC-FLOW-016.2 No review.md yet

- **GIVEN** a change with no review.md
- **WHEN** a finding is added
- **THEN** review.md is created from its template, with the finding as R1 under `## Findings`

#### Scenario: AC-FLOW-016.3 A Decision

- **GIVEN** an open finding R1 of type `quality`
- **WHEN** its decision is `back to design: return the token`, then is decided again as `accepted: rare enough`
- **THEN** after the first it is routed to design; after the second it has one Decision line, `accepted: rare enough`, and is ticked

#### Scenario: AC-FLOW-016.4 Done in a step, and confirmed

- **GIVEN** an open finding R1 routed back to specify
- **WHEN** `done in specify: added AC-X-001.2` is recorded, then it is closed as confirmed
- **THEN** after the first it is routed to design and still open; after the second it is ticked, and the review gate has no open finding

#### Scenario: AC-FLOW-016.5 What is refused

- **WHEN** a finding is added with an unknown type, a decision is neither `back to <step>:` nor `accepted:`, a step is unknown, the text is empty, or the finding is not in review.md
- **THEN** it is refused naming the problem and review.md is unchanged

#### Scenario: AC-FLOW-016.6 Other text is kept

- **GIVEN** a review.md with a hand-written finding using a `*` bullet and a bold ID, free text and HTML comments
- **WHEN** a Decision is written to that finding
- **THEN** only the new line is added: every other line, the comments included, is byte for byte as before
