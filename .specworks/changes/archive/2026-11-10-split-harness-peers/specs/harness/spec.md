# Delta: harness

## MODIFIED Requirements

### Requirement: REQ-HARNESS-001 One peer per skill

The harness session SHALL hold the user as peer zero, a backend, and one peer
for every packaged skill, named after the skill without its `specworks-` prefix
(`specworks-test` is `test`). Each skill's peer SHALL be of its own kind,
defined in its own module of the harness's peers package named after the peer,
and the harness's list of peer kinds SHALL match the packaged skills one to one.
Each skill peer's instructions SHALL be the harness preamble (REQ-HARNESS-004)
followed by the skill's text exactly as the installed skills are built from it
(its shared parts filled in), with no other change.

#### Scenario: AC-HARNESS-001.1 Every skill is a peer

- **WHEN** a harness session is built
- **THEN** its peers are the user, and one peer per packaged skill named `adopt`, `baseline`, `build`, ... `validate`, and nothing else answers

#### Scenario: AC-HARNESS-001.2 The skill unchanged

- **WHEN** the peer `test` is built
- **THEN** its instructions end with the packaged `specworks-test` skill text, shared parts filled in, character for character

#### Scenario: AC-HARNESS-001.3 A kind and a module per peer

- **WHEN** a harness session is built
- **THEN** no two skill peers are of the same kind, and the kind of the peer `<name>` is defined in the peers package's module `<name>`

#### Scenario: AC-HARNESS-001.4 Peer kinds match the skills

- **WHEN** the harness's list of peer kinds is compared with the packaged skills
- **THEN** every packaged skill has exactly one peer kind, and every peer kind serves a packaged skill

### Requirement: REQ-HARNESS-004 Moving on by default

The harness preamble SHALL tell the peer that it runs in a chat with no one
typing commands: at a stop whose question only offers the next step, it takes
the recommended option and hands over to the peer of that skill with the change
ref; at any other question its skill asks, it asks the user with `ask_user` and
waits; and `stop here` ends the run without handing over. The preamble SHALL
name the peers and say that `/specworks-<name>` in its skill means the peer
`<name>`. Only the peer whose skill merges a worktree's branch (`build`) SHALL also be
told that, where its skill merges, it asks the user to run `/merge <name>` and
waits, because only the user merges.

#### Scenario: AC-HARNESS-004.1 The preamble

- **WHEN** any skill peer is built
- **THEN** its instructions start with the preamble, which names every peer and states the three rules

#### Scenario: AC-HARNESS-004.2 A question for the user

- **GIVEN** a scripted `refine` that calls `ask_user` and then hands over
- **WHEN** the user answers the question in the chat
- **THEN** the agent gets the answer, and the hand-over follows it

#### Scenario: AC-HARNESS-004.3 The merge rule

- **WHEN** the skill peers are built
- **THEN** the preamble of `build` tells it to ask the user to run `/merge <name>` and wait, and no other peer's preamble mentions `/merge`
