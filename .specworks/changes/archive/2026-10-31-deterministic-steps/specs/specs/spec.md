# Spec Delta: specs

## ADDED Requirements

### Requirement: REQ-SPECS-015 A code task that waits on the test half

`check` SHALL warn, without failing, when a `[code]` task names the number of
a `[test]` task of the same change, naming both tasks, and when a `[code]`
task requires the suite (`specworks run test`), naming the task. Each warning
SHALL say that the code half is verified by lint, typecheck or observable
behaviour and that the suite runs after the merge. A `[test]` task naming a
`[code]` task, a `[code]` task naming another `[code]` task or a task with no
half, and a number that is not a task of the change SHALL not be warned
about.

#### Scenario: AC-SPECS-015.1 A code task naming a test task

- **GIVEN** tasks `1.1 [test] Wording checks; verify they fail before 1.2` and `1.2 [code] Write the skill; verify the 1.1 checks pass`
- **WHEN** `check` runs
- **THEN** it passes with a warning on task 1.2's line naming tasks 1.2 and 1.1, and none for task 1.1

#### Scenario: AC-SPECS-015.2 A code task requiring the suite

- **GIVEN** a task `1.3 [code] Implement; verify specworks run test passes`
- **WHEN** `check` runs
- **THEN** it passes with a warning on that line naming task 1.3 and the suite

#### Scenario: AC-SPECS-015.3 What is not warned about

- **GIVEN** tasks `1.1 Add stubs`, `1.2 [test] ...`, `2.1 [code] ...` and `2.2 [code] Follow 2.1 and 1.1; works on Python 3.11`
- **WHEN** `check` runs
- **THEN** it gives no warning about task 2.2
