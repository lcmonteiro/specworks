# harness

## Purpose

Runs the specworks flow as a chatinho chat: every packaged skill is a Deep Agent
peer that hands work to the next one by message, working in git workspaces that
the repository backend creates and merges, with the conversation kept in the
change's folder and the model read from the environment.

## Requirements

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

### Requirement: REQ-HARNESS-002 A peer is a Deep Agent

Each skill peer SHALL be a chatinho deep agent peer and SHALL run every message
it acts on as one run of a LangChain Deep Agent built with the session's model
and its instructions, whose file tools work in its own workspace at `/` and
read every other workspace under `/peers/<name>/`. Its tools SHALL be
`hand_over`, `ask_<peer>` for every other skill peer, `ask_user`, a
`run_<command>` tool for each command of the session, the deep agent's file
tools, and a `ws_<operation>` tool for each workspace operation the file tools
do not cover, `ws_run` among them. Its memory SHALL be the conversation as the
backend keeps it. A run that fails SHALL end in an error reply naming the kind
of failure, never a key.

#### Scenario: AC-HARNESS-002.1 A question answered

- **GIVEN** a scripted model that answers `done`
- **WHEN** the user asks the peer `refine` a question
- **THEN** one agent run happens with the `refine` instructions, and the reply to the question is `done`

#### Scenario: AC-HARNESS-002.2 Its tools

- **WHEN** the peer `build` runs
- **THEN** its model is given `hand_over`, `ask_test`, `ask_code`, `ask_user`, `run_merge`, `run_ws`, `ws_run`, `read_file`, `write_file` and `edit_file`, and no `ask_build`

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

### Requirement: REQ-HARNESS-005 Talking to a peer

A question the user addresses to a peer by name (`@test <text>` in the
terminal) SHALL be answered by that peer's run, as a reply to the question.

#### Scenario: AC-HARNESS-005.1 @test

- **WHEN** the user asks `test` "add a case for an empty file"
- **THEN** the peer `test` runs on that text and its answer replies to the question

### Requirement: REQ-HARNESS-006 Workspaces

The harness session SHALL have a chatinho workspace provider. The workspace of
every skill peer but `test` SHALL be the main checkout, which each of them may
write. The workspace of `test` SHALL be a git worktree on the branch
`peer/test`, created the first time it is asked for, from the commit the main
checkout has at that moment on the branch it has checked out then, and reused
while it exists, in this run or a later one. The worktree MUST NOT appear as an
untracked file of the main checkout. chatinho's `/ws` command SHALL list the
workspaces and show their diffs.

#### Scenario: AC-HARNESS-006.1 The test worktree

- **GIVEN** a main checkout on branch `add-x`
- **WHEN** the peer `test` writes `tests/test_x.py`
- **THEN** the file is in a worktree on branch `peer/test` started at `add-x`'s commit, not in the main checkout, and `git status` of the main checkout is clean

#### Scenario: AC-HARNESS-006.2 The phase peers share the checkout

- **WHEN** the peer `refine` writes `notes.md` and then the peer `specify` reads `/notes.md`
- **THEN** `specify` reads what `refine` wrote, and the file is in the main checkout

#### Scenario: AC-HARNESS-006.3 The base follows the checkout

- **GIVEN** a run started on `main`, whose checkout then switched to a new branch `add-x` with a commit of its own
- **WHEN** the peer `test` asks for its workspace for the first time
- **THEN** `peer/test` starts at `add-x`'s commit

#### Scenario: AC-HARNESS-006.4 Reused

- **GIVEN** the workspace of `test` with a commit in it, from an earlier run
- **WHEN** a new run's `test` asks for its workspace
- **THEN** it gets the same worktree with that commit

#### Scenario: AC-HARNESS-006.5 Listed

- **WHEN** the user runs `/ws` while `test`'s worktree has one commit
- **THEN** the answer lists `test`, `peer/test` and one commit ahead

### Requirement: REQ-HARNESS-007 Merging a workspace

The `merge <name>` command SHALL merge the branch of `<name>`'s worktree into
the main checkout the way `specworks merge` does for the run's change
(REQ-FLOW-015), only when the user runs it, and reply with what was merged and
resolved; after a merge it SHALL remove the worktree and its branch. On a
conflict it SHALL leave the main checkout and the worktree as they were and
reply with an error listing the conflicting files. Run by a peer, by a model
through its `run_merge` tool, when the run has no change yet, or for a name
with no worktree, it SHALL be refused with an error, changing nothing.

#### Scenario: AC-HARNESS-007.1 Merged

- **GIVEN** `test`'s worktree with a committed test file
- **WHEN** the user runs `/merge test`
- **THEN** the main checkout has the file, the worktree and the branch `peer/test` are gone, and the reply says merged

#### Scenario: AC-HARNESS-007.2 A conflict

- **GIVEN** the main checkout and `test`'s worktree both changed `src/a.py` differently
- **WHEN** the user runs `/merge test`
- **THEN** the reply is an error naming `src/a.py`, the main checkout is at its commit with no merge in progress, and the worktree still exists

#### Scenario: AC-HARNESS-007.3 Unknown

- **WHEN** the user runs `/merge nope`
- **THEN** the reply is an error saying there is no workspace `nope`

#### Scenario: AC-HARNESS-007.4 A model cannot merge

- **GIVEN** `test`'s worktree with a committed test file
- **WHEN** the peer `build` runs `merge test` through its `run_merge` tool
- **THEN** it gets an error saying only the user can merge, and the main checkout and the worktree are unchanged

#### Scenario: AC-HARNESS-007.5 No change yet

- **GIVEN** a run that has no change yet
- **WHEN** the user runs `/merge test`
- **THEN** the reply is an error saying the run has no change, and nothing is merged

### Requirement: REQ-HARNESS-008 Staying in the workspace

A peer's file tools SHALL work only in the workspaces the provider gives it: a
path that leads outside them SHALL be answered with an error and change
nothing, and writing under `/peers/<name>/` SHALL be refused. Its `ws_run`
tool SHALL run a command with its workspace's folder as the working folder,
with an environment that holds no `SPECWORKS_MODEL_*` or `SPECWORKS_LANGFUSE_*`
variable, and SHALL return its output and exit code; it SHALL refuse, without
running it, a command that runs git's `push` subcommand, and SHALL stop a
command still running after 600 seconds with an error. A refusal SHALL be an
error the agent sees.

#### Scenario: AC-HARNESS-008.1 Outside the workspace

- **WHEN** a peer reads or writes `/../outside.txt` or a path outside its workspace
- **THEN** it gets an error, and no file outside is read or written

#### Scenario: AC-HARNESS-008.2 The command's folder

- **GIVEN** the peer `test`
- **WHEN** it runs a command with `ws_run` that prints the folder it runs in, as the operating system reports it
- **THEN** that folder resolves to `test`'s worktree, on every platform

#### Scenario: AC-HARNESS-008.3 No push

- **WHEN** a peer runs `git push`, `git push origin main` or `git -C . push` with `ws_run`
- **THEN** it gets an error and nothing runs, while `git stash push -m wip` and `git commit -m "push later"` run

#### Scenario: AC-HARNESS-008.4 Another peer's workspace

- **WHEN** the peer `build` writes `/peers/test/x.py`
- **THEN** it gets an error saying the workspace is read-only, and `test`'s worktree is unchanged

#### Scenario: AC-HARNESS-008.5 A command that runs too long

- **GIVEN** a time limit made short for the test
- **WHEN** a peer runs a command with `ws_run` that sleeps past it
- **THEN** it gets an error saying the command was stopped, and the command is no longer running

### Requirement: REQ-HARNESS-009 The conversation kept

The backend SHALL append every message of the chat, one JSON line each with its
id, sender, addressee, reply, status and text, to `chat.jsonl` in the run's
change folder, and SHALL make the change folder's `.gitignore` name
`chat.jsonl`. A run SHALL start with no change and an empty conversation. Until
the run has a change, the backend SHALL hold the messages and write them, in
order, once the run's change is known: the first active change whose folder
changes during the run, whether it was created during the run or existed
before. A new run SHALL NOT load an earlier conversation. A failure to write
SHALL never stop the chat.

#### Scenario: AC-HARNESS-009.1 Appended

- **GIVEN** a run on change `add-x`
- **WHEN** the user says something and a peer replies
- **THEN** `chat.jsonl` in `add-x`'s folder ends with those two messages, and `git status` does not list it

#### Scenario: AC-HARNESS-009.2 Before the change exists

- **GIVEN** a run started with no change
- **WHEN** the user asks `refine` to start one and a peer creates the change `add-x` during the run
- **THEN** `add-x`'s `chat.jsonl` holds every message from the user's first one on, in order

#### Scenario: AC-HARNESS-009.4 A log that cannot be written

- **GIVEN** a change whose `chat.jsonl` is a folder
- **WHEN** a message is said
- **THEN** the chat goes on and the message is delivered

#### Scenario: AC-HARNESS-009.5 An existing change continued

- **GIVEN** an active change `add-x` whose `chat.jsonl` holds an earlier conversation
- **WHEN** a new run starts and a peer writes a file in `add-x`'s folder
- **THEN** the peers' memory did not hold the earlier conversation, and `add-x`'s `chat.jsonl` gains every message of this run after the earlier ones

### Requirement: REQ-HARNESS-010 The model from the environment

The harness SHALL use the model named by `SPECWORKS_MODEL_MODEL` with the key in
`SPECWORKS_MODEL_API_KEY`, or, when that key is missing or empty, the key of a
stored Copilot login (REQ-HARNESS-012), at `SPECWORKS_MODEL_BASE_URL` when it is
set, through an OpenAI-compatible API. A missing or empty model SHALL be an error
naming the variable. A missing or empty key with no stored login SHALL be an
error naming `SPECWORKS_MODEL_API_KEY` and saying to run `specworks login
copilot`. Both SHALL be raised before the session starts. A key's value, and a
login's tokens, SHALL never appear in any output, error, file or message.

#### Scenario: AC-HARNESS-010.1 Read from the environment

- **GIVEN** the three variables set
- **WHEN** the harness builds its model
- **THEN** the model uses that name, that base URL and that key

#### Scenario: AC-HARNESS-010.2 A missing variable

- **WHEN** `SPECWORKS_MODEL_MODEL` is missing or empty, or `SPECWORKS_MODEL_API_KEY` is missing or empty and no login is stored
- **THEN** building fails with an error naming that variable, and, for the key, saying to run `specworks login copilot`

#### Scenario: AC-HARNESS-010.3 The key never shown

- **GIVEN** a key `sk-secret` and a model that fails
- **WHEN** a peer runs and the conversation is written
- **THEN** `sk-secret` appears in no reply, error, log line or `chat.jsonl`

#### Scenario: AC-HARNESS-010.4 A login's tokens never shown

- **GIVEN** a stored login whose OAuth token is `gho_secret`, a session token `tid=secret`, and a model that fails
- **WHEN** a peer runs and the conversation is written
- **THEN** neither token appears in any reply, error, log line or `chat.jsonl`

### Requirement: REQ-HARNESS-011 The Copilot login

The harness SHALL let a user log in to GitHub Copilot with GitHub's device flow:
it SHALL show the verification address and the one-time code, wait until the user
authorises, and keep only the resulting long-lived OAuth token, readable by its
owner only, together with the GitHub Enterprise host when one is given. A login
SHALL have a scope: global, found from every project, or local, found only from
the project it was made in. A local login SHALL be kept outside the project's
folder, so no token is ever written inside the project. Logging in again in a
scope that holds a login that still gives a Copilot session token SHALL reuse it
without the device flow, unless forced; a stored login that no longer gives one
SHALL be replaced by a new device flow. A flow that is denied, or whose code
expires, SHALL fail and leave any earlier login as it was. No token, OAuth or
session, SHALL appear in any output, error or log.

#### Scenario: AC-HARNESS-011.1 A global login

- **WHEN** a user logs in with global scope and authorises in the device flow
- **THEN** the OAuth token is stored, readable by its owner only, and a project in any folder finds it

#### Scenario: AC-HARNESS-011.2 A local login

- **GIVEN** projects `a` and `b`
- **WHEN** a user logs in with local scope from project `a`
- **THEN** project `a` finds the login, project `b` does not, and no file is written inside `a`'s folder

#### Scenario: AC-HARNESS-011.3 An existing login is reused

- **GIVEN** a stored login in the chosen scope whose token still gives a session token
- **WHEN** the user logs in again in that scope
- **THEN** no device flow starts, the result says the login was reused, and the stored login is unchanged

#### Scenario: AC-HARNESS-011.4 A forced login

- **GIVEN** a stored login that still works
- **WHEN** the user logs in again, forcing it
- **THEN** a device flow runs and its token replaces the stored one

#### Scenario: AC-HARNESS-011.5 A stale login

- **GIVEN** a stored login whose token GitHub no longer accepts
- **WHEN** the user logs in again
- **THEN** a device flow runs and its token replaces the stored one

#### Scenario: AC-HARNESS-011.6 A flow that does not finish

- **GIVEN** a stored login
- **WHEN** a new device flow (forced) is denied, or its code expires
- **THEN** the login fails with an error and the earlier login is unchanged

#### Scenario: AC-HARNESS-011.7 GitHub Enterprise

- **WHEN** a user logs in with the host `example.ghe.com`
- **THEN** the device flow and every later token exchange go to that host, and the host is kept with the login

#### Scenario: AC-HARNESS-011.8 No token shown

- **GIVEN** an OAuth token `gho_secret` and a session token `tid=secret`
- **WHEN** a login runs, succeeds or fails
- **THEN** neither token appears in any output, error or log line

### Requirement: REQ-HARNESS-012 The model from a stored login

When `SPECWORKS_MODEL_API_KEY` is missing or empty, the harness SHALL use the
Copilot login stored for the project (REQ-HARNESS-011), the project's local one
before the global one, and SHALL use the Copilot API as the base URL, unless
`SPECWORKS_MODEL_BASE_URL` is set. Its key SHALL be a Copilot session token
exchanged from the OAuth token, never stored, and renewed before it expires, so
a chat that runs longer than one token's life goes on without a new login. The
harness SHALL NOT read or use any stored login when `SPECWORKS_MODEL_API_KEY` is
set. A stored login that can no longer give a session token SHALL be an error,
raised before the session starts when it is already known then, saying to run
`specworks login copilot` again, without any token.

#### Scenario: AC-HARNESS-012.1 The key from the login

- **GIVEN** a stored login, `SPECWORKS_MODEL_MODEL` set and `SPECWORKS_MODEL_API_KEY` unset
- **WHEN** the harness builds its model
- **THEN** the model uses that name, the Copilot API base and the session token exchanged from the stored OAuth token

#### Scenario: AC-HARNESS-012.2 Local before global

- **GIVEN** a global login and a local login of the project, for different accounts
- **WHEN** the harness builds its model
- **THEN** the session token is the one exchanged from the local login's token

#### Scenario: AC-HARNESS-012.3 An explicit key wins

- **GIVEN** `SPECWORKS_MODEL_API_KEY` set and a stored login
- **WHEN** the harness builds its model
- **THEN** the model uses the variable's key, and no stored login is read and no exchange is made

#### Scenario: AC-HARNESS-012.4 A long chat

- **GIVEN** a session token that expires in 25 minutes
- **WHEN** a request is sent after it has expired
- **THEN** a new session token is exchanged first and the request is sent with it, with no login

#### Scenario: AC-HARNESS-012.5 A login that no longer works

- **GIVEN** a stored login whose token GitHub rejects
- **WHEN** the harness needs a session token
- **THEN** it fails with an error saying to run `specworks login copilot` again, and no token appears in it

#### Scenario: AC-HARNESS-012.6 The base URL set by the user

- **GIVEN** a stored login and `SPECWORKS_MODEL_BASE_URL` set
- **WHEN** the harness builds its model
- **THEN** the model's base URL is the variable's value
