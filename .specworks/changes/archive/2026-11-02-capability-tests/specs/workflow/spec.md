## ADDED Requirements

### Requirement: REQ-FLOW-017 The review gate's tests

The review gate SHALL run only the tests of the capabilities the change
touched: those with a delta spec in the change, and those with a changed file
(as `specworks review` reports them) under the capability's code path or test
folder, in any module. It SHALL run each touched capability's module's
`test_scoped` command once, for that module's touched test folders, and pass
only when every run passes, naming the folders it ran. It SHALL run the full
suite (`commands.test`) instead when a touched capability's module has no
`test_scoped` command, when the change touches no capability, or when a touched
capability's test folder does not exist, the last with a warning naming each
missing folder. Validate SHALL keep running the full suite.

#### Scenario: AC-FLOW-017.1 Only the touched capability's tests

- **GIVEN** `commands.test_scoped` set, capabilities `auth` and `billing` with test folders `tests/auth` and `tests/billing`, and a change with a delta spec for `auth` and no changed file under `billing`
- **WHEN** the review gate runs
- **THEN** it runs `test_scoped` for `tests/auth` only, its check names `tests/auth`, and a failing test in `tests/billing` does not fail it

#### Scenario: AC-FLOW-017.2 A changed file touches its capability

- **GIVEN** `commands.test_scoped` set and a change with a delta spec for `auth` only
- **WHEN** the change also changes a file under `billing`'s code path, or under `tests/billing`
- **THEN** the review gate runs `test_scoped` for `tests/auth` and `tests/billing`

#### Scenario: AC-FLOW-017.3 No scoped test command

- **GIVEN** a project with `commands.test` and no `commands.test_scoped`
- **WHEN** the review gate runs
- **THEN** it runs the full suite as before, with no warning about test folders

#### Scenario: AC-FLOW-017.4 A touched capability without a test folder

- **GIVEN** `commands.test_scoped` set, and a change that touches `auth` and `billing`, where `tests/auth` does not exist
- **WHEN** the review gate runs
- **THEN** it runs the full suite (`commands.test`) and warns, without blocking, that `tests/auth` does not exist

#### Scenario: AC-FLOW-017.5 No capability touched

- **GIVEN** `commands.test_scoped` set and a change whose only changed files are outside every capability's code path and test folder (an integration test in `tests/`, a README), with no delta spec
- **WHEN** the review gate runs
- **THEN** it runs the full suite

#### Scenario: AC-FLOW-017.6 Failing scoped tests

- **GIVEN** `commands.test_scoped` set and a failing test in a touched capability's folder
- **WHEN** the review gate runs
- **THEN** it fails on that run; with `--allow-open` and an open finding in review.md, the failure is a warning

#### Scenario: AC-FLOW-017.7 A touched capability in another module

- **GIVEN** module `billing` at `services/billing` with its own `test_scoped`, and a top-level change with a delta spec for `billing:invoices` and one for top-level `auth`
- **WHEN** the review gate runs
- **THEN** it runs billing's `test_scoped` in `services/billing` for its `invoices` folder and the top level's for `tests/auth`, and passes only when both pass

#### Scenario: AC-FLOW-017.8 Validate runs everything

- **GIVEN** `commands.test_scoped` set and a change that touches `auth` only
- **WHEN** `specworks validate` runs
- **THEN** it runs the full suite (`commands.test`), and a failing test in `tests/billing` fails it

## MODIFIED Requirements

### Requirement: REQ-FLOW-011 Gate review

The review gate SHALL require review.md with no open finding (with
`--allow-open`, open findings are a warning), every changed file without tags
and every deleted source or test file named as a whole path under "Changed
files without tags", `@req` code for every requirement, an `@ac` test for
every criterion, no unknown tags, no tags left to removed requirements, and passing
tests: the tests REQ-FLOW-017 picks. With `--allow-open` and at least one open finding,
failing tests SHALL be a warning instead of blocking: the findings carry it to
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
