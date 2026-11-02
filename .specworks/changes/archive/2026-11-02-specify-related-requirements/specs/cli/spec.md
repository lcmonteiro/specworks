# Spec Delta: cli

## ADDED Requirements

### Requirement: REQ-CLI-016 spec find

`spec find <term>...` SHALL print each living requirement REQ-SPECS-016
finds, one line per requirement with its capability ref, ID, title and the
matching line's `path:line`, the path relative to the workspace root, and
`no requirement mentions <terms>` when there is none. Under `--json` it
SHALL print `{"terms": [...], "matches": [...]}` with each match's
`capability`, `id`, `title`, `path`, `line` and `text`. With no term it
SHALL be refused.

#### Scenario: AC-CLI-016.1 Matches as text

- **WHEN** `spec find "config set"` runs and two requirements mention it
- **THEN** it prints two lines, each with the capability, the ID, the title and `path:line`

#### Scenario: AC-CLI-016.2 Matches as JSON

- **WHEN** `spec find --json "config set"` runs
- **THEN** it prints `terms` and `matches`, each match with `capability`, `id`, `title`, `path` relative to the workspace root, `line` and `text`

#### Scenario: AC-CLI-016.3 No match

- **WHEN** `spec find nothing-like-this` runs
- **THEN** it prints `no requirement mentions nothing-like-this` and exits 0; under `--json` `matches` is empty

#### Scenario: AC-CLI-016.4 No term

- **WHEN** `spec find --json` runs with no term
- **THEN** it prints `{"error": ...}` and exits 1
