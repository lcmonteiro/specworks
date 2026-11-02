## MODIFIED Requirements

### Requirement: REQ-FLOW-010 Reading review.md

The system SHALL read each finding in review.md as a checkbox with its ID
(`- [ ] R<n>`, also `*`, `1.` and a bold ID), open or done, with a type (the
first bold word that is a known type, in any case). It SHALL route the finding
to the step of its type (`test-gap` to the test half, `code-gap`, `tag` and
`quality` to the code half), or to the step of a `back to <step>:` in its own
block, where a step is specify, design, implement (both halves), test, code
or review. A `back to <step>:`, `back to design only:` or `done in <step>:`
SHALL count only where it starts a line's text, after the line's indentation,
an optional bullet and an optional bold label (such as `**Decision**:` or
`**Proposal**:`); later on a line, and on the finding's own line, it is text.
After a `done in <step>:` it SHALL route the finding to the step
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

#### Scenario: AC-FLOW-010.9 A quoted form

- **GIVEN** a `quality` finding whose own line quotes `'back to design only:'`, whose Proposal is `back to code: name 'back to design only:' in the help`, and whose `confirmed in review:` line quotes `done in test:`
- **WHEN** it is read
- **THEN** it is routed to code, not design-only, and has no `done in` step; a finding of the same type with no Proposal is routed to code by its type

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
edited text does not read back with the expected finding. A form quoted
in a finding's text or Proposal SHALL route it only as REQ-FLOW-010 reads it:
by the form a line starts with, else by the finding's type.

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

- **WHEN** a finding is added with an unknown type, a decision is none of `back to <step>:`, `back to design only:` and `accepted:`, a step is unknown, the text is empty, or the finding is not in review.md
- **THEN** it is refused naming the problem and review.md is unchanged

#### Scenario: AC-FLOW-016.6 Other text is kept

- **GIVEN** a review.md with a hand-written finding using a `*` bullet and a bold ID, free text and HTML comments
- **WHEN** a Decision is written to that finding
- **THEN** only the new line is added: every other line, the comments included, is byte for byte as before

#### Scenario: AC-FLOW-016.7 A design-only Decision

- **GIVEN** an open finding R1 of type `design-gap`
- **WHEN** its decision is `back to design only: reword Decisions > Matching`, and another finding's is `back to code only: rename x`
- **THEN** R1 has that Decision and is routed to design; the second is refused naming the forms a decision can take, and review.md is unchanged

#### Scenario: AC-FLOW-016.8 Adding a finding that quotes a form

- **GIVEN** a review.md with no findings
- **WHEN** a `quality` finding is added with the text `list 'back to design only:' in the help` and the proposal `add it after 'back to <step>:'`, and a second one with the proposal `back to test: assert 'done in code:' is read`
- **THEN** both are added; the first is routed to code by its type and is not design-only, and the second is routed to test
