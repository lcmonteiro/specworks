# Spec Delta: harness

## MODIFIED Requirements

### Requirement: REQ-HARNESS-004 Moving on by default

The harness preamble SHALL tell the peer that it runs in a chat with no one
typing commands: at a stop whose question only offers the next step, it takes
the recommended option and hands over to the peer of that skill with the change
ref; at any other question its skill asks, it asks the user with `ask_user` and
waits; and `stop here` ends the run without handing over. The preamble SHALL
name the peers and say that `/specworks-<name>` in its skill means the peer
`<name>`. Only the peers whose skill merges a worktree's branch (`build` and
`autopilot`) SHALL also be told that, where their skill merges, they ask the
user to run `/merge <name>` and wait, because only the user merges.

#### Scenario: AC-HARNESS-004.1 The preamble

- **WHEN** any skill peer is built
- **THEN** its instructions start with the preamble, which names every peer and states the three rules

#### Scenario: AC-HARNESS-004.2 A question for the user

- **GIVEN** a scripted `refine` that calls `ask_user` and then hands over
- **WHEN** the user answers the question in the chat
- **THEN** the agent gets the answer, and the hand-over follows it

#### Scenario: AC-HARNESS-004.3 The merge rule

- **WHEN** the skill peers are built
- **THEN** the preambles of `build` and `autopilot` tell them to ask the user to run `/merge <name>` and wait, and no other peer's preamble mentions `/merge`
