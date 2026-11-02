# Spec Delta: workflow

## MODIFIED Requirements

### Requirement: REQ-FLOW-010 Reading review.md

The system SHALL read each finding in review.md as a checkbox with its ID
(`- [ ] R<n>`, also `*`, `1.` and a bold ID), open or done, with a type (the
first bold word that is a known type, in any case). It SHALL route the finding
to the step of its type (`test-gap` to the test half, `code-gap`, `tag` and
`quality` to the code half), or to the step of a `back to <step>:` in its own
block, where a step is specify, design, implement (both halves), test, code
or review. After a `done in <step>:` it SHALL route the finding to the step
after that one: design after specify, implement after design, and review
after implement, test or code, except that a finding whose Decision says
`back to design only:` SHALL be routed to design, and after `done in design:`
to review. HTML comments and code fences SHALL be ignored.
A checkbox outside a finding's block (at the top level or indented, ticked or
not), and an open finding with no known type or step, SHALL be reported as
unreadable.

#### Scenario: AC-FLOW-010.1 Finding variants

- **WHEN** a finding is written with `*`, a numbered bullet or a bold ID
- **THEN** it is read as finding R1

#### Scenario: AC-FLOW-010.2 Unreadable checkboxes

- **WHEN** review.md has a checkbox that is not `R<n> …`, or an open finding of unknown type with no `back to`
- **THEN** the review gate and validate fail on readability, even with `--allow-open`

#### Scenario: AC-FLOW-010.3 Types and routing

- **WHEN** a finding's bold type is in another case or after another bold word, or its block says `back to <step>:`
- **THEN** it is routed to that type's or that `back to` step; prose like "goes back to design" does not route it

#### Scenario: AC-FLOW-010.4 Code fences

- **WHEN** a finding appears in a code fence, or a fence or sub-checkbox sits under a finding
- **THEN** the fenced finding is an example, and the finding above the fence stays open and routed

#### Scenario: AC-FLOW-010.5 A checkbox indented outside any finding

- **GIVEN** review.md with `- Follow-ups:` followed by `  - [ ] reset still ignores case`, and no finding above it
- **WHEN** it is read
- **THEN** the checkbox is reported as unreadable, so the review gate fails (also with `--allow-open`); the same checkbox under a finding stays part of that finding

#### Scenario: AC-FLOW-010.6 Routing to the halves

- **WHEN** open findings are a `test-gap`, a `code-gap`, and one saying `back to implement:`
- **THEN** they are routed to test, to code, and to implement (both halves)

#### Scenario: AC-FLOW-010.7 Done in a step

- **WHEN** findings say `done in design:`, `done in test:` and `done in code:`
- **THEN** the first is routed to implement and the other two to review

#### Scenario: AC-FLOW-010.8 Design only

- **WHEN** a finding's Decision says `back to design only:`, and later `done in design:` is added under it
- **THEN** it is routed to design, and then to review instead of implement; a finding saying `back to design:` is routed to implement after `done in design:`, as before

### Requirement: REQ-FLOW-012 Build cycles

After a review, the system SHALL say which steps the next build cycle runs,
from the open findings: design when any finding needs design; both halves
(test and code, in parallel) when a finding needs design without `only` or
needs implement; otherwise only the halves the findings need; and review last. It
SHALL say the phase the cycle starts at: design when design is in the cycle,
implement when a half is, review otherwise. A spec finding SHALL hand over to
`/specworks-specify` instead of starting a cycle. A change with no review.md,
or no open finding, has no next cycle.

#### Scenario: AC-FLOW-012.1 No cycle

- **WHEN** the change has no review.md, or every finding is done
- **THEN** there is no start and no steps

#### Scenario: AC-FLOW-012.2 Only the half that needs it

- **WHEN** the open findings are code findings only (or test findings only)
- **THEN** the cycle starts at implement with the steps code, review (or test, review)

#### Scenario: AC-FLOW-012.3 Back to overrides the type

- **WHEN** a finding's Decision says `back to design:`
- **THEN** the cycle starts at design with the steps design, test, code, review, whatever its type

#### Scenario: AC-FLOW-012.4 A spec finding

- **WHEN** an open finding is a spec-gap
- **THEN** the cycle starts at specify with no steps and hands over to `/specworks-specify`

#### Scenario: AC-FLOW-012.5 Done in a step

- **WHEN** the only open findings say `done in design:` (or `done in code:`)
- **THEN** the cycle starts at implement with the steps test, code, review (or at review with the step review)

#### Scenario: AC-FLOW-012.6 Both halves

- **WHEN** the open findings are a test finding and a code finding, or one finding says `back to implement:`
- **THEN** the cycle starts at implement with the steps test, code, review

#### Scenario: AC-FLOW-012.7 Design only

- **WHEN** the only open findings say `back to design only:`, before or after their `done in design:`
- **THEN** the cycle starts at design with the steps design, review before it, and at review with the step review after it; with a code finding as well, the steps are design, code, review; with a finding saying `back to design:` as well, they are design, test, code, review

### Requirement: REQ-FLOW-016 Writing findings to review.md

The system SHALL write a change's review findings as review.md text that
REQ-FLOW-010 reads back: a new finding under `## Findings` with the next free
ID, its type and its Proposal (creating review.md from its template when
missing); a finding's Decision, replacing the one it has, which SHALL start
with `back to <step>:`, `back to design only:` or `accepted:` and, when `accepted`, tick the finding;
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

#### Scenario: AC-FLOW-016.7 A design-only Decision

- **GIVEN** an open finding R1 of type `design-gap`
- **WHEN** its decision is `back to design only: reword Decisions > Matching`, and another finding's is `back to code only: rename x`
- **THEN** R1 has that Decision and is routed to design; the second is refused naming the forms a decision can take, and review.md is unchanged
