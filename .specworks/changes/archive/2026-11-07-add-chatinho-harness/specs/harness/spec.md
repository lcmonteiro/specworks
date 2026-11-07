# Spec Delta: harness

## Purpose

Runs the specworks flow as a chatinho chat: every packaged skill is a Deep Agent
peer that hands work to the next one by message, working in git workspaces that
the repository backend creates and merges, with the conversation kept in the
change's folder and the model read from the environment.

## ADDED Requirements

### Requirement: REQ-HARNESS-001 One peer per skill

The harness session SHALL hold the user as peer zero, a backend, and one peer
for every packaged skill, named after the skill without its `specworks-` prefix
(`specworks-test` is `test`). Each skill peer's instructions SHALL be the harness
preamble (REQ-HARNESS-004) followed by the skill's text exactly as the installed
skills are built from it (its shared parts filled in), with no other change.

#### Scenario: AC-HARNESS-001.1 Every skill is a peer

- **WHEN** a harness session is built
- **THEN** its peers are the user, and one peer per packaged skill named `adopt`, `baseline`, `build`, ... `validate`, and nothing else answers

#### Scenario: AC-HARNESS-001.2 The skill unchanged

- **WHEN** the peer `test` is built
- **THEN** its instructions end with the packaged `specworks-test` skill text, shared parts filled in, character for character

### Requirement: REQ-HARNESS-002 A peer is a Deep Agent

Each skill peer SHALL run every message it acts on as one run of a LangChain
Deep Agent built with the session's model, its instructions, and its tools:
`hand_over`, `ask_<peer>` for every other skill peer, `ask_user`, the
`workspace` and `merge` commands, and file and shell tools in its workspace. Its
memory SHALL be the conversation as the backend keeps it. A run that fails SHALL
end in an error reply naming the kind of failure, never a key.

#### Scenario: AC-HARNESS-002.1 A question answered

- **GIVEN** a scripted model that answers `done`
- **WHEN** the user asks the peer `refine` a question
- **THEN** one agent run happens with the `refine` instructions, and the reply to the question is `done`

#### Scenario: AC-HARNESS-002.2 Its tools

- **WHEN** the peer `build` runs
- **THEN** its model is given `hand_over`, `ask_test`, `ask_code`, `ask_user`, the workspace, merge, file and shell tools, and no `ask_build`

#### Scenario: AC-HARNESS-002.3 A failed run

- **GIVEN** a scripted model that raises an authentication error
- **WHEN** the peer `refine` is asked
- **THEN** the reply has status error, names the failure, and holds no key value

### Requirement: REQ-HARNESS-003 Handing over by message

A peer's `hand_over(peer, text)` SHALL say `text` addressed to that peer, as a
reply to the message the peer is acting on, and return without waiting. A skill
peer SHALL start a run on a say addressed to it, and SHALL treat a say addressed
to another peer, or to nobody from another peer, as memory only. Handing over to
an unknown peer or to itself SHALL return an error to the agent and say nothing.

#### Scenario: AC-HARNESS-003.1 The next peer starts

- **GIVEN** a scripted `refine` that hands over to `specify`
- **WHEN** the user's request reaches `refine`
- **THEN** a message from `refine` to `specify`, replying to the request, is said, and `specify` runs on it

#### Scenario: AC-HARNESS-003.2 No nesting

- **GIVEN** peers that hand over in a chain longer than the session's ask depth
- **WHEN** the first one starts
- **THEN** every peer in the chain runs, and none fails for depth

#### Scenario: AC-HARNESS-003.3 Not addressed

- **WHEN** a peer says something addressed to `specify`
- **THEN** no other skill peer runs

#### Scenario: AC-HARNESS-003.4 An unknown peer

- **WHEN** a peer hands over to `nobody` or to itself
- **THEN** the agent gets an error naming the peer, and nothing is said

### Requirement: REQ-HARNESS-004 Moving on by default

The harness preamble SHALL tell the peer that it runs in a chat with no one
typing commands: at a stop whose question only offers the next step, it takes
the recommended option and hands over to the peer of that skill with the change
ref; at any other question its skill asks, it asks the user with `ask_user` and
waits; `stop here` ends the run without handing over. The preamble SHALL name
the peers and say that `/specworks-<name>` in its skill means the peer `<name>`.

#### Scenario: AC-HARNESS-004.1 The preamble

- **WHEN** any skill peer is built
- **THEN** its instructions start with the preamble, which names every peer and states the three rules

#### Scenario: AC-HARNESS-004.2 A question for the user

- **GIVEN** a scripted `refine` that calls `ask_user` and then hands over
- **WHEN** the user answers the question in the chat
- **THEN** the agent gets the answer, and the hand-over follows it

### Requirement: REQ-HARNESS-005 Talking to a peer

A question the user addresses to a peer by name (`@test <text>` in the
terminal) SHALL be answered by that peer's run, as a reply to the question.

#### Scenario: AC-HARNESS-005.1 @test

- **WHEN** the user asks `test` "add a case for an empty file"
- **THEN** the peer `test` runs on that text and its answer replies to the question

### Requirement: REQ-HARNESS-006 Workspaces

The `workspace <name>` command SHALL create a git worktree on a new branch
`<branch>--<name>` started from the main checkout's current commit, where
`<branch>` is the main checkout's branch, in a git-ignored folder of the
repository, and SHALL make it the invoking peer's workspace; when the workspace
exists it SHALL reuse it. `workspace main` SHALL make the main checkout the
peer's workspace again. A peer's workspace SHALL be the main checkout until it
changes it. A name that is not lowercase letters, digits and hyphens SHALL be
refused.

#### Scenario: AC-HARNESS-006.1 A new workspace

- **GIVEN** a main checkout on branch `add-x`
- **WHEN** the peer `test` invokes `workspace test-half`
- **THEN** a worktree on branch `add-x--test-half` exists at the main checkout's commit, `git status` of the main checkout is clean, and `test`'s file tools now work in it

#### Scenario: AC-HARNESS-006.2 Reused

- **GIVEN** the workspace `test-half` with a commit in it
- **WHEN** another peer invokes `workspace test-half`
- **THEN** it gets the same worktree with that commit, and its workspace is now that one

#### Scenario: AC-HARNESS-006.3 Back to main

- **WHEN** a peer in `test-half` invokes `workspace main`
- **THEN** its file tools work in the main checkout again

#### Scenario: AC-HARNESS-006.4 A bad name

- **WHEN** a peer invokes `workspace ../x` or `workspace Test`
- **THEN** it gets an error naming the rule, and no worktree or branch is made

### Requirement: REQ-HARNESS-007 Merging a workspace

The `merge <name>` command SHALL merge the workspace's branch into the main
checkout the way `specworks merge` does for the run's change (REQ-FLOW-015), and
reply with what was merged and resolved; after a merge it SHALL remove the
worktree and its branch, and peers in it SHALL go back to the main checkout. On
a conflict it SHALL leave the main checkout and the workspace as they were and
reply with an error listing the conflicting files, to the peer that invoked it.
An unknown workspace SHALL be refused.

#### Scenario: AC-HARNESS-007.1 Merged

- **GIVEN** a workspace `test-half` with a committed test file
- **WHEN** a peer invokes `merge test-half`
- **THEN** the main checkout has the file, the worktree and the branch `<branch>--test-half` are gone, and the reply says merged

#### Scenario: AC-HARNESS-007.2 A conflict

- **GIVEN** the main checkout and the workspace both changed `src/a.py` differently
- **WHEN** a peer invokes `merge test-half`
- **THEN** the reply is an error naming `src/a.py`, the main checkout is at its commit with no merge in progress, and the workspace still exists

#### Scenario: AC-HARNESS-007.3 Unknown

- **WHEN** a peer invokes `merge nope`
- **THEN** it gets an error saying there is no workspace `nope`

### Requirement: REQ-HARNESS-008 Staying in the workspace

A peer's file tools SHALL resolve every path inside its workspace and refuse a
path that leads outside it. Its shell tool SHALL run each command with the
workspace as its working folder and SHALL refuse a `git push` command. A refusal
SHALL be an error the agent sees, and SHALL change nothing.

#### Scenario: AC-HARNESS-008.1 Outside the workspace

- **WHEN** a peer reads or writes `../outside.txt` or an absolute path outside its workspace
- **THEN** it gets an error, and no file outside is read or written

#### Scenario: AC-HARNESS-008.2 The shell's folder

- **GIVEN** a peer in the workspace `test-half`
- **WHEN** it runs `pwd` with its shell tool
- **THEN** the output is that workspace's folder

#### Scenario: AC-HARNESS-008.3 No push

- **WHEN** a peer runs `git push` or `git push origin main` with its shell tool
- **THEN** it gets an error, and nothing runs

### Requirement: REQ-HARNESS-009 The conversation kept

The backend SHALL append every message of the chat, one JSON line each with its
id, sender, addressee, reply, status and text, to `chat.jsonl` in the run's
change folder, and SHALL make the change folder's `.gitignore` name
`chat.jsonl`. Until the run has a change, the backend SHALL hold the messages
and write them, in order, once the run's change exists: the one named by
`--change`, else the first change created during the run. At start, the backend
SHALL give back the messages of the change's `chat.jsonl`, so a new run
continues the conversation. A failure to write SHALL never stop the chat.

#### Scenario: AC-HARNESS-009.1 Appended

- **GIVEN** a run on change `add-x`
- **WHEN** the user says something and a peer replies
- **THEN** `chat.jsonl` in `add-x`'s folder ends with those two messages, and `git status` does not list it

#### Scenario: AC-HARNESS-009.2 Before the change exists

- **GIVEN** a run started with a request and no change
- **WHEN** a peer creates the change `add-x` during the run
- **THEN** `add-x`'s `chat.jsonl` holds every message from the request on, in order

#### Scenario: AC-HARNESS-009.3 Continued

- **GIVEN** a change whose `chat.jsonl` holds an earlier conversation
- **WHEN** a run starts on that change
- **THEN** the peers' memory holds that conversation, and new messages are appended after it

#### Scenario: AC-HARNESS-009.4 A log that cannot be written

- **GIVEN** a change whose `chat.jsonl` is a folder
- **WHEN** a message is said
- **THEN** the chat goes on and the message is delivered

### Requirement: REQ-HARNESS-010 The model from the environment

The harness SHALL use the model named by `SPECWORKS_MODEL_MODEL` with the key in
`SPECWORKS_MODEL_API_KEY`, at `SPECWORKS_MODEL_BASE_URL` when it is set, through
an OpenAI-compatible API. A missing or empty key or model SHALL be an error
naming the variable, raised before the session starts. A key's value SHALL never
appear in any output, error, file or message.

#### Scenario: AC-HARNESS-010.1 Read from the environment

- **GIVEN** the three variables set
- **WHEN** the harness builds its model
- **THEN** the model uses that name, that base URL and that key

#### Scenario: AC-HARNESS-010.2 A missing variable

- **WHEN** `SPECWORKS_MODEL_API_KEY` or `SPECWORKS_MODEL_MODEL` is missing or empty
- **THEN** building fails with an error naming that variable

#### Scenario: AC-HARNESS-010.3 The key never shown

- **GIVEN** a key `sk-secret` and a model that fails
- **WHEN** a peer runs and the conversation is written
- **THEN** `sk-secret` appears in no reply, error, log line or `chat.jsonl`
