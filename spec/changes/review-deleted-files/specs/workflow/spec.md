# Spec Delta: workflow

## MODIFIED Requirements

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
