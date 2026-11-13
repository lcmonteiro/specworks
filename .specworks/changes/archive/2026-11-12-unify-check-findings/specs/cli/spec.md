# Spec Delta: cli

## ADDED Requirements

### Requirement: REQ-CLI-024 validate --write

`specworks validate --write` SHALL validate the change and write its
validation.md (REQ-FLOW-019), printing the verdict as validate does and the
path of validation.md relative to the workspace root (`"path"` under
`--json`). It SHALL exit 1 on FAIL, as validate does, after writing.
Without `--write`, `specworks validate` SHALL write no file.

#### Scenario: AC-CLI-024.1 Writing on FAIL

- **WHEN** `specworks validate --write --json` runs on a change with an open `[code]` task
- **THEN** it exits 1, prints the FAIL verdict and `.specworks/changes/active/<name>/validation.md` as its path, and that file holds a finding routed to code

#### Scenario: AC-CLI-024.2 Writing on PASS

- **WHEN** `specworks validate --write` runs on a change that passes
- **THEN** it exits 0 and validation.md says `None.` under Findings

#### Scenario: AC-CLI-024.3 No write without the flag

- **WHEN** `specworks validate` runs without `--write` on a change that fails
- **THEN** it exits 1 and no validation.md is created

## MODIFIED Requirements

### Requirement: REQ-CLI-011 finding

`specworks finding` SHALL write a change's findings (REQ-FLOW-016)
through `add <type> <text> --proposal <proposal> [--artifact <check artifact>]
[--suggestion <file> --lang <language>]`,
`decide <id> <decision>`, `done <id> --in <step> <text>` and
`close <id> <text>`, each with `--change` (the change's ref) and `--json`.
`add` SHALL write to the check artifact named by `--artifact` (`review` when
omitted); `decide`, `done` and `close` SHALL write to the check artifact
whose letter the ID starts with. `--suggestion` SHALL read the suggestion
from the file (`-` for standard input), `--lang` naming its fence's language
(`text` when omitted); a missing file SHALL be refused. Each SHALL print the finding as `specworks
cycle` reads it afterwards (its ID, open or done, and the step it is routed
to) and the path of the artifact it wrote, relative to the workspace root; a refusal
SHALL be an error (`{"error": …}` with exit 1 under `--json`) and change no
file.

#### Scenario: AC-CLI-011.1 The four commands

- **WHEN** `finding add`, `finding decide`, `finding done` and `finding close` run in turn on one change with `--json`
- **THEN** each exits 0 and prints the finding with its ID, state and step, and review.md's path relative to the workspace root

#### Scenario: AC-CLI-011.2 A refusal

- **WHEN** `finding decide R9 "accepted: x"` runs for a finding that does not exist, with `--json`
- **THEN** it prints `{"error": …}` naming R9, exits 1, and review.md is unchanged

#### Scenario: AC-CLI-011.3 A finding in validation.md

- **WHEN** `finding add code-gap "x" --proposal "back to code: y" --artifact validation --json`, then `finding close V1 "passes" --json` run on one change
- **THEN** both exit 0 and print V1 with validation.md's path relative to the workspace root, and review.md is not created

#### Scenario: AC-CLI-011.4 An unknown artifact

- **WHEN** `finding add code-gap "x" --proposal "back to code: y" --artifact tasks --json` runs
- **THEN** it prints `{"error": …}` naming the check artifacts, exits 1, and no file changes

#### Scenario: AC-CLI-011.5 A suggestion from a file

- **WHEN** `finding add code-gap "x" --proposal "back to code: y" --artifact inspection --suggestion fix.diff --lang diff --json` runs, then the same with a file that does not exist
- **THEN** the first exits 0 and inspection.md holds the file's text under `**Suggestion**:` in a `diff` fence; the second prints `{"error": …}` naming the file, exits 1, and no file changes
