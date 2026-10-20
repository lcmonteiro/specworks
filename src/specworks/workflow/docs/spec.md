# workflow

## Purpose

The workflow a change goes through: its artifacts and how to write them, the
gates each phase must pass, starting a phase, the review of drift between specs
and code, build cycles, and the final validate report.

## Requirements

### Requirement: REQ-FLOW-001 Artifact states

The system SHALL report each artifact of a change (refinement, proposal, specs,
design, tasks, traceability, review) as `done` when its file exists, as
`skipped` for the delta specs of a change marked skip-specs, and otherwise as
`ready` when every artifact it requires is done, optional or skipped, or as
`blocked`.

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

### Requirement: REQ-FLOW-002 Instructions for an artifact

The system SHALL give, for each artifact of a change, the path to write it to,
its template and instruction, the context inherited by the change's module, and
its dependencies with whether each is done. For the delta specs, it SHALL also
list the workspace's capabilities with their next free requirement ID. An
unknown artifact SHALL be refused, naming the known ones.

#### Scenario: AC-FLOW-002.1 Output path and template

- **WHEN** the instructions for an artifact (e.g. refinement, review) are requested
- **THEN** they name its output path in the change folder, its template and instruction, and whether it exists

#### Scenario: AC-FLOW-002.2 Inherited context

- **GIVEN** a change in a module
- **WHEN** its instructions are requested
- **THEN** their context holds the top level's context and the module's

#### Scenario: AC-FLOW-002.3 Capabilities for the delta specs

- **WHEN** the instructions for the delta specs are requested
- **THEN** they list each capability with its next free ID (e.g. `REQ-AUTH-003`)

#### Scenario: AC-FLOW-002.4 Unknown artifact

- **WHEN** the instructions for an artifact that does not exist are requested
- **THEN** the request fails with `unknown artifact` and the list of artifacts

### Requirement: REQ-FLOW-003 Gates in common

The system SHALL run a gate as a list of named checks and pass it when no
blocking check fails. Warnings never block. Every gate SHALL require valid specs
and report `specworks check` warnings without blocking. With `--no-run`, the
project's commands SHALL not run and their checks are reported as warnings.
With `--fresh`, each command SHALL run again once per invocation instead of
reusing an earlier result. A phase with no gate SHALL be refused.

#### Scenario: AC-FLOW-003.1 Invalid specs

- **WHEN** a change's specs are invalid (e.g. no SHALL, or a missing proposal)
- **THEN** the design and test gates fail on `specs and tasks are valid`

#### Scenario: AC-FLOW-003.2 Without running the commands

- **WHEN** a gate or validate runs with `--no-run`
- **THEN** the command checks are non-blocking and say they were not run

#### Scenario: AC-FLOW-003.3 Fresh runs

- **WHEN** a gate, validate or `start` runs with `--fresh`
- **THEN** each command runs again once, and no result says `same code as the run at`

#### Scenario: AC-FLOW-003.4 Unknown gate

- **WHEN** the gate of a phase that has none is requested (e.g. `deploy`)
- **THEN** it fails with `no gate for phase 'deploy'`

### Requirement: REQ-FLOW-004 Gate specify

The specify gate SHALL pass when the specs and tasks are valid and tasks.md is
written. An acceptance criterion that no task covers SHALL be reported once.

#### Scenario: AC-FLOW-004.1 A complete plan

- **WHEN** a change has a proposal, valid delta specs and tasks
- **THEN** the specify gate passes

#### Scenario: AC-FLOW-004.2 No tasks

- **WHEN** tasks.md is missing
- **THEN** the gate fails on `tasks.md is written`

#### Scenario: AC-FLOW-004.3 A criterion without a task

- **WHEN** no task names a criterion
- **THEN** the gate fails and reports that criterion once

### Requirement: REQ-FLOW-005 Specs as agreed

When a change leaves specify through `start`, the system SHALL record a
fingerprint of each requirement. Later gates SHALL warn, without blocking, about
each requirement changed, added or dropped since, and say how to accept the new
specs. Spacing alone SHALL not count as a change. Starting design again SHALL
accept the current specs. A change that never left specify through `start` is
not checked.

#### Scenario: AC-FLOW-005.1 Changed and added

- **GIVEN** a change that started design
- **WHEN** a requirement is edited and another added
- **THEN** the gate warns `REQ-… changed` and `REQ-… added`, and names `specworks start design` to accept them

#### Scenario: AC-FLOW-005.2 Dropped

- **WHEN** a requirement is removed from the delta specs after specify
- **THEN** the gate warns `REQ-… dropped`

#### Scenario: AC-FLOW-005.3 Spacing is not a change

- **WHEN** only spacing or blank lines change in a requirement
- **THEN** the check passes

#### Scenario: AC-FLOW-005.4 Accepting new specs

- **WHEN** the change starts design again after its specs changed
- **THEN** the check passes again

#### Scenario: AC-FLOW-005.5 Moved by hand

- **GIVEN** a change moved to design with `specworks phase`, never through `start`
- **WHEN** its gate runs
- **THEN** the check is not shown

### Requirement: REQ-FLOW-006 Gate design

The design gate SHALL require an Interfaces section in design.md (found by its
heading in any case, HTML comments and code fences ignored), with every file
named in its code spans existing inside the change's module folder, written
relative to that folder or to the workspace root. `None` SHALL pass without files, and prose
naming no file SHALL be a warning. It SHALL run the build and typecheck commands
when they are configured. The existing test suite must pass, except once the
change already has `@ac` tests, when a red suite is only a warning.

#### Scenario: AC-FLOW-006.1 The Interfaces section

- **WHEN** design.md has no Interfaces heading, or only a template comment under it
- **THEN** the gate fails on the Interfaces check; a heading like `## Interfaces (API)` or `## interfaces` counts

#### Scenario: AC-FLOW-006.2 Named files exist

- **WHEN** the Interfaces section names files in code spans (`src/auth/reset.py:ResetService`)
- **THEN** the gate fails listing those that do not exist, and passes once they do; names without a folder count only with a code extension

#### Scenario: AC-FLOW-006.3 None and prose

- **WHEN** the section says `None`, or describes the API without any file
- **THEN** the gate passes; prose without files is a non-blocking warning

#### Scenario: AC-FLOW-006.4 The existing tests

- **WHEN** the test suite fails and the change has no `@ac` tests of its own
- **THEN** the gate fails; once the change has `@ac` tests, the failure is a warning saying so

#### Scenario: AC-FLOW-006.5 Build and typecheck

- **WHEN** `build` and `typecheck` are configured
- **THEN** they run as checks of their own, and none are shown when they are not configured

#### Scenario: AC-FLOW-006.6 A file outside the change's module

- **GIVEN** a change in module `billing` (at `services/billing`) whose Interfaces name `src/invoices.py`, and a `src/invoices.py` that exists only at the workspace root
- **WHEN** the design gate runs
- **THEN** it fails listing `src/invoices.py`; it passes once the file exists in the module, named either `src/invoices.py` or `services/billing/src/invoices.py`

### Requirement: REQ-FLOW-007 Gate test

The test gate SHALL require an `@ac` test for every acceptance criterion and no
tag to an unknown ID. It SHALL warn, without blocking, about an `@ac` tag outside
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

### Requirement: REQ-FLOW-008 Gate code

The code gate SHALL require every task done, `@req` code for every requirement,
an `@ac` test for every criterion, no unknown tags, no tags left to removed
requirements or to criteria a MODIFIED block drops, and a passing test suite
(which needs a configured test command).

#### Scenario: AC-FLOW-008.1 Everything done

- **WHEN** every task is ticked, everything is tagged and the tests pass
- **THEN** the gate passes and shows the command it ran

#### Scenario: AC-FLOW-008.2 What is missing

- **WHEN** a requirement has no `@req` code and tasks are open
- **THEN** the gate fails listing the requirement and the open tasks

#### Scenario: AC-FLOW-008.3 Failing tests

- **WHEN** the test command fails (even with output that is not text)
- **THEN** the gate fails with the command's output

#### Scenario: AC-FLOW-008.4 No test command

- **WHEN** no test command is configured
- **THEN** the gate fails with `no 'test' command configured`

#### Scenario: AC-FLOW-008.5 Removed and dropped

- **WHEN** code or tests are still tagged with a removed requirement, its criteria, or a criterion a MODIFIED block drops
- **THEN** the code gate fails listing them (the test gate only warns), and passes once they are gone

### Requirement: REQ-FLOW-009 Drift report

`specworks review` SHALL compare the files changed since the merge base with the
base branch (committed, uncommitted and untracked; workflow folders left out),
classify each as source, test or other, and report untagged source and test
files next to the spec-side gaps. A file deleted on the branch SHALL be listed
with kind `deleted` and the kind it had, and a deleted source or test file SHALL
be reported as a drift candidate. The base SHALL default to origin's default
branch, then `origin/main`, `main`, `origin/master`, `master`. On the base
branch itself, the diff SHALL start at the commit before the change was created.
Without git, or without a base, only the spec side SHALL be checked, with a note
saying why.

#### Scenario: AC-FLOW-009.1 No drift

- **WHEN** every changed file is tagged
- **THEN** there are no findings, and each changed file is listed with its kind; workflow files are not

#### Scenario: AC-FLOW-009.2 Untagged code and tests

- **WHEN** source or test files changed (modified or untracked) without tags
- **THEN** they are listed as untraced; a changed doc is listed as `other`, not as a finding

#### Scenario: AC-FLOW-009.3 Spec-side gaps

- **WHEN** a requirement has no code, criteria have no tests, or a tag is unknown
- **THEN** they are reported with the untraced files

#### Scenario: AC-FLOW-009.4 No git or no base

- **WHEN** there is no git repository, the given base does not exist, or no default base is found
- **THEN** changed files are unknown and the note says why (or asks for `--base`)

#### Scenario: AC-FLOW-009.5 On the base branch

- **WHEN** HEAD is on the base branch
- **THEN** the diff starts at the commit before the change's metadata was added; with no such commit, the note says only uncommitted files are compared

#### Scenario: AC-FLOW-009.6 Non-ASCII names

- **WHEN** a changed file's name has non-ASCII characters
- **THEN** it is listed by its real name

#### Scenario: AC-FLOW-009.7 Deleted files

- **WHEN** the branch deletes a source file, a test file and a doc
- **THEN** each is listed with kind `deleted` and the kind it had (`source`, `test`, `other`); the source and test files are reported under `deletedFiles`, the doc is not

### Requirement: REQ-FLOW-010 Reading review.md

The system SHALL read each finding in review.md as a checkbox with its ID
(`- [ ] R<n>`, also `*`, `1.` and a bold ID), open or done, with a type (the
first bold word that is a known type, in any case). It SHALL route the finding
to the phase of its type, or to the phase of a `back to <phase>:` in its own
block, and after a `done in <phase>:` to the phase after that one. HTML comments
and code fences SHALL be ignored. A top-level checkbox that is not a finding,
and an open finding with no known type or phase, SHALL be reported as
unreadable.

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

### Requirement: REQ-FLOW-011 Gate review

The review gate SHALL require review.md with no open finding (with
`--allow-open`, open findings are a warning), every changed file without tags
and every deleted source or test file named as a whole path under "Changed
files without tags", and the code gate's
tag and test checks. It SHALL warn about each MODIFIED requirement whose
behaviour changed while none of its tests changed, and about a diff that may be
incomplete because HEAD is on the base branch.

#### Scenario: AC-FLOW-011.1 review.md

- **WHEN** review.md is missing, or has an open finding
- **THEN** the gate fails, listing the open finding; it passes once findings are resolved

#### Scenario: AC-FLOW-011.2 In a build

- **WHEN** the gate runs with `--allow-open`
- **THEN** open findings are a non-blocking warning, and every other check still blocks

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

### Requirement: REQ-FLOW-012 Build cycles

After a review, the system SHALL say where the next build cycle starts: the
earliest phase any open finding needs, with the phases from there to review. A
spec finding SHALL hand over to `/specworks-specify` instead of starting a cycle.
A change with no review.md, or no open finding, has no next cycle.

#### Scenario: AC-FLOW-012.1 No cycle

- **WHEN** the change has no review.md, or every finding is done
- **THEN** there is no start and no phases

#### Scenario: AC-FLOW-012.2 The earliest phase wins

- **WHEN** open findings need different phases (code, test, design)
- **THEN** the cycle starts at the earliest and runs every phase after it up to review

#### Scenario: AC-FLOW-012.3 Back to overrides the type

- **WHEN** a finding's Decision says `back to design:`
- **THEN** the cycle starts at design, whatever its type

#### Scenario: AC-FLOW-012.4 A spec finding

- **WHEN** an open finding is a spec-gap
- **THEN** the cycle starts at specify with no phases and hands over to `/specworks-specify`

#### Scenario: AC-FLOW-012.5 Done in a phase

- **WHEN** a finding says `done in <phase>:`
- **THEN** it needs the phase after that one (`specify` -> design, `design` -> test, `code` -> review)

### Requirement: REQ-FLOW-013 Validate

`specworks validate` SHALL run grouped checks (completeness, correctness,
coherence), each naming the phase skill that fixes a failure, and give a PASS
verdict when no blocking check fails. It SHALL run the test command (lint and
typecheck when configured) and check that diagram SVGs are up to date. It SHALL
write nothing. Not having gone through review is a warning. `gate validate`
SHALL apply the same checks.

#### Scenario: AC-FLOW-013.1 A finished change

- **WHEN** a reviewed change is validated
- **THEN** the verdict is PASS, every check has a group, and an unconfigured lint is reported as `not configured`

#### Scenario: AC-FLOW-013.2 Read-only

- **WHEN** validate and `gate validate` run
- **THEN** no file of the project changes

#### Scenario: AC-FLOW-013.3 Where to go back

- **WHEN** checks fail (an open task, untagged requirement, missing review.md)
- **THEN** the verdict is FAIL and each failure names its phase skill; `goBackTo` lists them

#### Scenario: AC-FLOW-013.4 Failing commands

- **WHEN** the test or lint command fails
- **THEN** the check is critical and shows the command's output

#### Scenario: AC-FLOW-013.5 Outdated diagram

- **WHEN** a change's diagram has no SVG or an outdated one
- **THEN** the coherence check fails naming the SVG

#### Scenario: AC-FLOW-013.6 Review skipped

- **WHEN** the change never reached review
- **THEN** a non-blocking warning names its phase

#### Scenario: AC-FLOW-013.7 gate validate

- **WHEN** `gate validate` runs
- **THEN** it passes and fails as validate does

### Requirement: REQ-FLOW-014 Starting a phase

`specworks start <phase>` SHALL run the gates the phase depends on, in order,
and move the change only when they all pass. Moving forward, every phase left
behind that has a gate must pass. Re-entering a phase or going back for rework
needs only the gate just before it. It SHALL stop at the first failing gate,
naming the phase skill that fixes each failed check, and SHALL refuse `done`.

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
