# Spec Delta: integrations

## ADDED Requirements

### Requirement: REQ-INTEG-007 Includes with parameters

A skill's include line SHALL take parameters after the shared file's name,
`key=value` or `key="value with spaces"`, and each `{{key}}` in the shared
file SHALL be replaced by its value where the skill is filled in. An include
without parameters SHALL be filled in with the shared file as it is. A
`{{key}}` the include does not fill, or a key the shared file does not use,
SHALL fail, naming the skill, the shared file and the key, and
`specworks skills` and `specworks update` SHALL then write, change and
remove no skill.

#### Scenario: AC-INTEG-007.1 A parameter filled in

- **GIVEN** a shared file `Record it with --in {{phase}}.`
- **WHEN** a skill includes it with `phase=test`
- **THEN** the filled-in skill has `Record it with --in test.` in place of the include line

#### Scenario: AC-INTEG-007.2 A quoted value

- **GIVEN** a shared file with `{{who}}`
- **WHEN** a skill includes it with `who="the code half"`
- **THEN** the filled-in skill has `the code half` there

#### Scenario: AC-INTEG-007.3 A placeholder left unfilled

- **GIVEN** a shared file with `{{phase}}`
- **WHEN** a skill includes it with no parameters
- **THEN** filling it in fails naming the skill, the shared file and `phase`

#### Scenario: AC-INTEG-007.4 A key the shared file does not use

- **GIVEN** a shared file with no `{{colour}}`
- **WHEN** a skill includes it with `colour=red`
- **THEN** filling it in fails naming the skill, the shared file and `colour`

#### Scenario: AC-INTEG-007.5 An include without parameters

- **GIVEN** a shared file with no `{{`
- **WHEN** a skill includes it with no parameters
- **THEN** the filled-in skill has the shared file's text exactly

#### Scenario: AC-INTEG-007.6 Nothing written on a failure

- **GIVEN** a packaged skill whose include fails to fill in
- **WHEN** `specworks skills` runs
- **THEN** it exits 1 with the error, and no skill folder is written or changed

#### Scenario: AC-INTEG-007.7 The packaged skills

- **WHEN** every packaged skill is filled in
- **THEN** none fails and none has `{{` or an include line left

#### Scenario: AC-INTEG-007.8 Nothing written by update on a failure

- **GIVEN** installed skills, a stale `specworks-…` skill folder, and a packaged skill whose include fails to fill in
- **WHEN** `specworks update` runs
- **THEN** it fails with the error, and every file under the skills folders is unchanged, the stale folder included
