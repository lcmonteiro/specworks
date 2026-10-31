# Spec Delta: cli

## ADDED Requirements

### Requirement: REQ-CLI-011 finding

`specworks finding` SHALL write a change's review findings (REQ-FLOW-016)
through `add <type> <text> --proposal <proposal>`, `decide <id> <decision>`,
`done <id> --in <step> <text>` and `close <id> <text>`, each with `--change`
(the change's ref) and `--json`. Each SHALL print the finding as `specworks
cycle` reads it afterwards (its ID, open or done, and the step it is routed
to) and the path of review.md relative to the workspace root; a refusal
SHALL be an error (`{"error": …}` with exit 1 under `--json`) and change no
file.

#### Scenario: AC-CLI-011.1 The four commands

- **WHEN** `finding add`, `finding decide`, `finding done` and `finding close` run in turn on one change with `--json`
- **THEN** each exits 0 and prints the finding with its ID, state and step, and review.md's path relative to the workspace root

#### Scenario: AC-CLI-011.2 A refusal

- **WHEN** `finding decide R9 "accepted: x"` runs for a finding that does not exist, with `--json`
- **THEN** it prints `{"error": …}` naming R9, exits 1, and review.md is unchanged
