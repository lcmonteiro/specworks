# Spec Delta: workflow

## MODIFIED Requirements

### Requirement: REQ-FLOW-001 Artifact states

The system SHALL report each artifact of a change (refinement, proposal, specs,
design, tasks, traceability, review, validation, inspection) as `done` when its file exists, as
`skipped` for the delta specs of a change marked skip-specs, and otherwise as
`ready` when every artifact it requires is done, optional or skipped, or as
`blocked`. For a change in implement, the status SHALL also report each half
(test, code) with its tasks done and its tasks in total, read from tasks.md
without running any command.

#### Scenario: AC-FLOW-001.1 After planning

- **GIVEN** a change with proposal, delta specs and tasks written
- **WHEN** its status is read
- **THEN** those are `done`, and refinement, design, traceability and review are `ready`

#### Scenario: AC-FLOW-001.2 A written refinement

- **WHEN** a change's refinement.md is written
- **THEN** its status shows refinement as `done`

#### Scenario: AC-FLOW-001.3 A change without behaviour change

- **GIVEN** a change marked skip-specs, with a proposal
- **WHEN** its status is read
- **THEN** specs is `skipped` and tasks is `ready`

#### Scenario: AC-FLOW-001.4 The halves of implement

- **GIVEN** a change in implement whose tasks.md has three `[test]` tasks, all done, and four `[code]` tasks, one done
- **WHEN** its status is read
- **THEN** it shows the test half at 3 of 3 tasks and the code half at 1 of 4; a change in another phase shows no halves

#### Scenario: AC-FLOW-001.5 Validation

- **GIVEN** a change with review.md written
- **WHEN** its status is read before and after validation.md is written
- **THEN** validation is `ready` and optional before, and `done` after

#### Scenario: AC-FLOW-001.6 Inspection

- **GIVEN** a change with tasks.md written
- **WHEN** its status is read before and after inspection.md is written
- **THEN** inspection is `ready` and optional before, and `done` after

### Requirement: REQ-FLOW-010 Reading findings

The system SHALL read each finding in a check artifact (REQ-FLOW-018) as a
checkbox with its ID, the artifact's letter and a number (`- [ ] R<n>` in
review.md, `- [ ] V<n>` in validation.md, `- [ ] I<n>` in inspection.md, also `*`, `1.` and a bold ID), open
or done, with a type (the first bold word that is a known type, in any case).
It SHALL route the finding to the step of its type (`spec-gap` to specify,
`design-gap` to design, `test-gap` to the test half, `code-gap`, `tag` and
`quality` to the code half, `question` to review), or to the step of a `back to <step>:` in its own
block, where a step is specify, design, implement (both halves), test, code
or review, and a `done in <step>:` step is one of these. A `back to <step>:`, `back to design only:` or `done in <step>:`
SHALL count only where it starts a line's text, after the line's indentation,
an optional bullet and an optional bold label (such as `**Decision**:` or
`**Proposal**:`); later on a line, and on the finding's own line, it is text.
After a `done in <step>:` it SHALL route the finding to the step
after that one: design after specify, implement after design, review
after implement, test or code, and after review the step that confirms it:
inspect for a finding of inspection.md, validate for any other, except that a finding whose Decision says
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

#### Scenario: AC-FLOW-010.10 Back to review

- **WHEN** a `code-gap` finding's Decision says `back to review: account for a.py`
- **THEN** it is routed to review; `back to review only:` is not a route

#### Scenario: AC-FLOW-010.11 Done in review

- **WHEN** validation.md has a `code-gap` V1 with `done in code:` and a `quality` V2 saying `back to review:`, and later `done in review:` is added under each
- **THEN** both are routed to review before, and to validate after, still open

#### Scenario: AC-FLOW-010.12 A question

- **WHEN** inspection.md has `- [ ] I1 **question** why is the token not returned?`
- **THEN** I1 is open and routed to review

#### Scenario: AC-FLOW-010.13 Back to inspect

- **WHEN** an inspection finding I1 of type `code-gap` gets `done in code:`, then `done in review:`
- **THEN** it is routed to code, then review, then inspect, still open; a validation finding with the same lines is routed to validate at the end

### Requirement: REQ-FLOW-012 Build cycles

After a review or a validate, the system SHALL say which steps the next build cycle runs,
from the open findings of every check artifact (REQ-FLOW-018), each listed
with its ID: design when any finding needs design; both halves
(test and code, in parallel) when a finding needs design without `only` or
needs implement; otherwise only the halves the findings need; and review last. It
SHALL say the phase the cycle starts at: design when design is in the cycle,
implement when a half is, review otherwise. A spec finding SHALL hand over to
`/specworks-specify` instead of starting a cycle. A finding routed to
validate or inspect SHALL start no cycle: it waits for that step to confirm it. A change with no check
artifact, or no open finding, has no next cycle. It SHALL also say the
change's next state: the phase the cycle starts at, or, with no cycle to run,
the phase after the change's current one (validate after review, close after
validate).

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

#### Scenario: AC-FLOW-012.8 Findings from validation.md

- **GIVEN** review.md with every finding done, and validation.md with an open `test-gap` V1
- **WHEN** the next cycle is read
- **THEN** it starts at implement with the steps test, review, and lists V1

#### Scenario: AC-FLOW-012.9 The next state

- **WHEN** the next state is read for a change in review with an open `code-gap`, in review with no open finding, and in validate with no open finding
- **THEN** it is implement, validate and close

#### Scenario: AC-FLOW-012.10 Waiting for validate

- **GIVEN** a change in review whose only open finding is a V1 with `done in review:`
- **WHEN** the next cycle is read
- **THEN** there is no start and no steps, V1 is listed routed to validate, and the next state is validate

#### Scenario: AC-FLOW-012.11 Waiting for inspect

- **GIVEN** a change in validate whose only open finding is an I1 with `done in review:`
- **WHEN** the next cycle is read
- **THEN** there is no start and no steps, I1 is listed routed to inspect, and the next state is close

### Requirement: REQ-FLOW-016 Writing findings

The system SHALL write a change's findings as text of their check artifact
(REQ-FLOW-018) that REQ-FLOW-010 reads back: a new finding under `## Findings`
of the artifact asked for (review.md when none is), with that artifact's
letter and its next free number, its type and its Proposal (creating the
artifact from its template when missing); and, for an existing finding,
found in the artifact its ID's letter names: its Decision, replacing the one it has, which SHALL start
with `back to <step>:`, `back to design only:` or `accepted:` and, when `accepted`, tick the finding;
a `done in <step>:` line, where the step may also be review; and a tick with what its step confirmed (`confirmed in review:`,
`confirmed in validate:` or `confirmed in inspect:`, after the artifact's step). It SHALL add
each line at the end of the finding's block and leave every other line of
the file as it was. It SHALL refuse an unknown finding, type, step or check
artifact, an
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

#### Scenario: AC-FLOW-016.9 A finding in validation.md

- **GIVEN** a change with review.md holding R1 and no validation.md
- **WHEN** a `code-gap` finding is added to validation, then marked `done in code:` by its ID
- **THEN** validation.md is created from its template with V1 under `## Findings`, routed to code and then to review, and review.md is unchanged

#### Scenario: AC-FLOW-016.10 An unknown check artifact

- **WHEN** a finding is added to `tasks`, or decided as `V7` in a change whose validation.md has no V7
- **THEN** it is refused naming the check artifacts (or V7), and no file changes

#### Scenario: AC-FLOW-016.11 Done in review

- **GIVEN** validation.md with an open V1 routed to review
- **WHEN** `done in review: a.py accounted for` is recorded under it
- **THEN** it is routed to validate and still open, and only that line is added

#### Scenario: AC-FLOW-016.12 A finding in inspection.md

- **GIVEN** a change with no inspection.md
- **WHEN** a `question` finding is added to inspection, then closed
- **THEN** inspection.md is created from its template with I1 under `## Findings`, routed to review; after the close it is ticked with `confirmed in inspect:`

### Requirement: REQ-FLOW-018 Check artifacts

The schema SHALL declare which artifacts of a change are check artifacts:
each with the letter of its finding IDs and the gates its open findings
block. It SHALL declare review (`review.md`, letter `R`, blocking the review
and validate gates) and validation (`validation.md`, letter `V`, blocking the
validate gate) and inspection (`inspection.md`, letter `I`, blocking no
gate), the last two optional. Every check artifact SHALL be read as
REQ-FLOW-010 says, with its own letter, and a finding whose ID has another
letter than its artifact's SHALL be reported as unreadable.

#### Scenario: AC-FLOW-018.1 The declared check artifacts

- **WHEN** the check artifacts are listed
- **THEN** they are review with letter `R`, blocking the review and validate gates, validation with letter `V`, blocking the validate gate, and inspection with letter `I`, blocking no gate

#### Scenario: AC-FLOW-018.2 A finding in validation.md

- **GIVEN** validation.md with `- [ ] V1 **code-gap** REQ-X-001 has no code` and `- [ ] V2 **quality** ...` whose block says `back to review: account for a.py`
- **WHEN** it is read
- **THEN** V1 is open and routed to code, and V2 is open and routed to review

#### Scenario: AC-FLOW-018.3 A letter from another artifact

- **WHEN** validation.md has a finding `- [ ] R1 **code-gap** ...`, or review.md one `- [ ] V1 **code-gap** ...`
- **THEN** it is reported as unreadable, and the gates that artifact blocks fail on readability

#### Scenario: AC-FLOW-018.4 Inspection findings block nothing

- **GIVEN** a change whose review gate and validate pass
- **WHEN** inspection.md gets an open finding I1
- **THEN** the review gate and validate still pass, with no check or warning about I1
