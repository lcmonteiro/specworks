## MODIFIED Requirements

### Requirement: REQ-FLOW-001 Artifact states

The system SHALL report each artifact of a change (refinement, proposal, specs,
design, tasks, traceability, review) as `done` when its file exists, as
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

### Requirement: REQ-FLOW-007 Gate test

The test gate SHALL check the test half of implement: it SHALL require every
`[test]` task done, an `@ac` test for every acceptance criterion and no tag to
an unknown ID. It SHALL warn, without blocking, about an `@ac` tag outside
test files and about removed requirements or criteria still tagged.

#### Scenario: AC-FLOW-007.1 Criteria without tests

- **WHEN** some criteria have no `@ac` tag
- **THEN** the gate fails listing them; it passes once every criterion is tagged

#### Scenario: AC-FLOW-007.2 Unknown IDs

- **WHEN** a test is tagged with a criterion no spec has
- **THEN** the gate fails naming the tag and where it is

#### Scenario: AC-FLOW-007.3 A tag in a source file

- **WHEN** an `@ac` tag of the change is in a source file
- **THEN** the gate passes with a warning naming the file and line

#### Scenario: AC-FLOW-007.4 Test tasks open

- **WHEN** a `[test]` task is not done, while `[code]` tasks may be open
- **THEN** the gate fails listing the open `[test]` tasks only; open `[code]` tasks do not affect it

### Requirement: REQ-FLOW-008 Gate code

The code gate SHALL check the code half of implement: it SHALL require every
`[code]` task done, `@req` code for every requirement, no unknown tags, no
tags left to removed requirements or to criteria a MODIFIED block drops, and
a configured test command whose run passes. It SHALL NOT require an `@ac`
test for every criterion. While the change has `@ac` tests of its own, a
failing run SHALL be a warning instead of blocking: those tests meet the code
in review.

#### Scenario: AC-FLOW-008.1 Everything done

- **WHEN** every `[code]` task is ticked, every requirement has `@req` code and the tests pass
- **THEN** the gate passes and shows the command it ran

#### Scenario: AC-FLOW-008.2 What is missing

- **WHEN** a requirement has no `@req` code and `[code]` tasks are open
- **THEN** the gate fails listing the requirement and the open `[code]` tasks; open `[test]` tasks are not listed

#### Scenario: AC-FLOW-008.3 Failing tests

- **GIVEN** a change with no `@ac` tests of its own
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

### Requirement: REQ-FLOW-010 Reading review.md

The system SHALL read each finding in review.md as a checkbox with its ID
(`- [ ] R<n>`, also `*`, `1.` and a bold ID), open or done, with a type (the
first bold word that is a known type, in any case). It SHALL route the finding
to the step of its type (`test-gap` to the test half, `code-gap`, `tag` and
`quality` to the code half), or to the step of a `back to <step>:` in its own
block, where a step is specify, design, implement (both halves), test, code
or review. After a `done in <step>:` it SHALL route the finding to the step
after that one: design after specify, implement after design, and review
after implement, test or code. HTML comments and code fences SHALL be ignored.
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

### Requirement: REQ-FLOW-011 Gate review

The review gate SHALL require review.md with no open finding (with
`--allow-open`, open findings are a warning), every changed file without tags
and every deleted source or test file named as a whole path under "Changed
files without tags", `@req` code for every requirement, an `@ac` test for
every criterion, no unknown tags, no tags left to removed requirements, and a
passing test suite. With `--allow-open` and at least one open finding, a
failing suite SHALL be a warning instead of blocking: the findings carry it to
the next cycle. It SHALL warn about each MODIFIED requirement whose behaviour
changed while none of its tests changed, and about a diff that may be
incomplete because HEAD is on the base branch.

#### Scenario: AC-FLOW-011.1 review.md

- **WHEN** review.md is missing, or has an open finding
- **THEN** the gate fails, listing the open finding; it passes once findings are resolved

#### Scenario: AC-FLOW-011.2 In a build

- **WHEN** the gate runs with `--allow-open`
- **THEN** open findings are a non-blocking warning, and every other check still blocks, except the suite as below

#### Scenario: AC-FLOW-011.3 Untagged files accounted for

- **WHEN** an untagged changed file is not named under "Changed files without tags" (only in a finding, a comment, or as part of a longer path)
- **THEN** the gate fails listing it; naming it there makes the gate pass

#### Scenario: AC-FLOW-011.4 MODIFIED behaviour needs changed tests

- **WHEN** a MODIFIED requirement's behaviour changed and none of its test files changed on the branch
- **THEN** the gate warns naming the requirement and its test files; a title-only change, or no git, shows no such check

#### Scenario: AC-FLOW-011.5 On the base branch

- **WHEN** HEAD is on the base branch with no commit marking the change's start
- **THEN** the gate warns that the change's commits are compared with nothing; on a branch, no such warning

#### Scenario: AC-FLOW-011.6 Deleted files accounted for

- **WHEN** a deleted source or test file is not named under "Changed files without tags"
- **THEN** the gate fails listing it; naming it there with a reason makes the gate pass

#### Scenario: AC-FLOW-011.7 Failing tests with open findings

- **GIVEN** review.md with an open finding and a failing test suite
- **WHEN** the gate runs with `--allow-open`
- **THEN** it passes with warnings for the open finding and the failing suite; without `--allow-open`, or with no open finding, the failing suite blocks

#### Scenario: AC-FLOW-011.8 Criteria without tests

- **WHEN** a criterion has no `@ac` test
- **THEN** the review gate fails listing it, also with `--allow-open`

### Requirement: REQ-FLOW-012 Build cycles

After a review, the system SHALL say which steps the next build cycle runs,
from the open findings: design when any finding needs design; both halves
(test and code, in parallel) when design is in the cycle or a finding needs
implement; otherwise only the halves the findings need; and review last. It
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

### Requirement: REQ-FLOW-014 Starting a phase

`specworks start <phase>` SHALL run the gates the phase depends on, in order,
and move the change only when they all pass. Moving forward, every phase left
behind that has a gate must pass; implement's gate is the test gate and then
the code gate, and `specworks gate implement` SHALL run both. Re-entering a
phase or going back for rework needs only the gate just before it. It SHALL
stop at the first failing gate, naming the phase skill that fixes each failed
check, and SHALL refuse `done`, and `test` or `code`, naming `implement`.

#### Scenario: AC-FLOW-014.1 The gates to run

- **WHEN** a change in one phase starts another
- **THEN** the gates are: none from refine; every phase left behind moving forward; only the one before when re-entering or going back

#### Scenario: AC-FLOW-014.2 Gates pass

- **WHEN** the gates pass
- **THEN** the change moves to the phase and the result lists the gates run

#### Scenario: AC-FLOW-014.3 A gate fails

- **WHEN** a gate fails, or the first of several fails
- **THEN** the change stays in its phase, and no later gate runs

#### Scenario: AC-FLOW-014.4 Done

- **WHEN** `start done` is requested
- **THEN** it is refused, naming `specworks close`

#### Scenario: AC-FLOW-014.5 Where to go back

- **WHEN** a gate run by `start` fails
- **THEN** each failed check names the phase skill that fixes it (`-> /specworks-code`)

#### Scenario: AC-FLOW-014.6 Leaving implement

- **GIVEN** a change in implement whose test half passes and whose code half has an open `[code]` task
- **WHEN** `start review` is requested
- **THEN** the test gate and the code gate run, the change stays in implement, and the result names the code gate as not passed

#### Scenario: AC-FLOW-014.7 Test and code are halves

- **WHEN** `start test` or `start code` is requested
- **THEN** it is refused, naming `implement`

#### Scenario: AC-FLOW-014.8 Gate implement

- **WHEN** `specworks gate implement` runs
- **THEN** it runs the test gate and the code gate and passes only when both pass
