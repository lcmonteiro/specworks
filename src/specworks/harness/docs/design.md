# Design: harness

## Overview

`specworks harness` (no argument, no option) opens the whole specworks flow as
an empty chatinho chat in the terminal; a change starts or continues when the
user messages a peer (`@refine <request>`, `@build go on with <change>`). The user is peer zero; every packaged skill is a
peer named after it without the `specworks-` prefix (`refine`, `specify`,
`build`, `test`, ...), each a chatinho `DeepAgentConnector` whose instructions
are a short harness preamble followed by the skill unchanged. Peers hand work
to each other by message. The phase peers share the main checkout; the `test`
peer works in its own git worktree, which only the user merges back with
`/merge test`. A run's conversation is kept in the folder of the change it works on. The package
`src/specworks/harness` needs the optional `harness` extra (chatinho with its
`tui` and `deepagents` extras) and is imported only by the
`harness` command.

- `session.py`: `build_harness` (the session: user, peers, workspace
  provider, backend, `/ws` and `/merge`), `run_harness`.
- `peers/`: `base.py` (`SkillPeer`, the pinned preamble, `MERGE_RULE`,
  `hand_over`), one module per skill (`<Name>Peer`), and `__init__.py`
  (`PEERS`, `worktree_peers`).
- `workspaces.py`: `SpecworksWorktrees` (the provider), `SpecworksWorkspace`
  (its `run` operation), `MergeCommand` (`/merge`).
- `confine.py`: the push refusal and the shell's environment.
- `backend.py`: `GitBackend` (`chat.jsonl`).
- `model.py`: `model_from_env`.
- `logins.py`: the stored Copilot login (`Login`, `LoginStore`, `config_dir`).
- `copilot.py`: the device-flow login, the session token and `log_in`.

![harness](diagrams/harness-blocks.svg)

## Decisions

### SkillPeer is a thin DeepAgentConnector

`SkillPeer(DeepAgentConnector)` passes `system_prompt=skill_instructions(...)`,
`ask_user=True`, the chat memory (the last 100 messages) and
`tools=[hand_over]`; the model's agent, its backend over the peer's workspace
(`/` its own, `/peers/<name>/` the others, read-only) and the `ws_<op>` tools
are chatinho's. It overrides only `answer()` (the run, then the recorded
hand-over) and `listen()` (does nothing: a skill peer acts only on what is
addressed to it). Keeping our own `AgentConnector.graph()` override with
`create_deep_agent` was rejected: it copied what chatinho now owns and could
not use its workspaces. chatinho is pinned to a commit. (add-chatinho-harness)

### A hand-over is said after the run, from a fresh context

`hand_over(peer, text)` checks the peer (a skill peer, not itself) and records
it; once `answer()` has its reply, the peer says the text to that peer,
replying to the message it answered, in a task created with a fresh
`contextvars.Context()`, so its depth starts at one. The reply is posted before
the next stage starts and no stage nests in another, so a full run never
reaches chatinho's `max_depth`. `build` and `done` keep using `ask_<peer>`,
which waits and nests one level, as the skills expect. Naming the next peer in
the text (`@specify ...`) was rejected: it bypasses chatinho's addressing.
(add-chatinho-harness)

![A hand-over between stages](diagrams/hand-over-flow.svg)

### One peer class per skill, each in its own module

`peers/` holds `base.py` (`SkillPeer` and everything the peers share), one
module `<name>.py` per packaged skill with one subclass `<Name>Peer`
decorated `@connector("<name>")` that sets only what differs from the base,
and `__init__.py` with `PEERS`, the classes in alphabetical order of name.
A class states its name once: its skill is `skill_name()` = `PREFIX + name`.
`build_harness` builds `cls(model, names)` for each of `PEERS`. A step's
specifics live on its class: `worktree` (only `TestPeer`, which also sets
`__test__ = False` so pytest does not collect it) and `rules`, preamble lines
after the common ones (only `BuildPeer`, `(MERGE_RULE,)`). Auto-discovery (a
registry plus `pkgutil`) was rejected as implicit and import-order dependent;
a settings table was rejected as not a class per step. That `PEERS` matches
`packaged_skills()` one to one is checked by a test, not at run time, so a
skill added without its class fails CI, not the chat. (split-harness-peers)

### The preamble, then the skill unchanged

`skill_instructions(skill, peers, rules=())` is `preamble(name, peers,
rules)`, a blank line, then `read_skill(skill)`. The preamble (`PREAMBLE` in
`peers/base.py`, pinned verbatim by a test) says that `/specworks-<name>`
means the peer `<name>`, that a question offering only the next step is
answered by taking the `(recommended)` option and calling `hand_over`, that
any other question goes to `ask_user`, and that `stop here` ends without a
hand-over; each of the peer's `rules` follows on its own line. No skill text
changes for the harness. (add-chatinho-harness) `MERGE_RULE` (a skill that
merges a worktree's branch asks the user to run `/merge <name>` instead of
merging) goes only to `build`, the one skill that merges a worktree's branch;
`done` merges specs at close, never a branch. (split-harness-peers)

### One shared checkout, one test worktree

`SpecworksWorktrees(GitWorktrees)` (`repo=ws.root`,
`workspace=SpecworksWorkspace`) gives every peer not in `self.worktrees`
(`worktree_peers(PEERS)`, the classes with `worktree`: `{"test"}`; taken from
the peers since split-harness-peers) the main checkout: one chatinho `Tree` for the whole provider
(one lock) whose base is `HEAD`, so its diff is the uncommitted work and stays
right when a skill switches the checkout's branch. It is writable
(`SpecworksWorkspace`) for a checkout peer and a read-only `WorkspaceView` for
`test` and for commands. `test` gets chatinho's worktree
`.chatinho/worktrees/test` on `peer/test`, started from the branch the
checkout has when it is created. `/ws` (chatinho's) lists and diffs the real
worktrees only. One worktree per peer, chatinho's default, was rejected: every
stage would need a merge. Overriding `provision` and building the checkout's
`Tree` rely on chatinho internals, which the pin keeps stable.
(add-chatinho-harness)

### The shell is a workspace operation

`SpecworksWorkspace.run(command)` is an `@operation(..., writes=True)`, so
agents get it as `ws_run` and it is serialised with the workspace's other
writes. It refuses a git push (`PUSH_RE`: `git`, any global options, then the
`push` subcommand, so `git stash push` and a commit message mentioning push
still run) with `PermissionError` before anything starts; otherwise it runs the
command through the platform shell in the workspace's folder with
`shell_env()` (the environment without `SPECWORKS_MODEL_*` and
`SPECWORKS_LANGFUSE_*`, so no key reaches the output), stderr merged into
stdout, and returns `exit code <n>\n<output>`. Past `RUN_TIMEOUT` (600 s, read
at call time) it kills the command (its whole process group on POSIX) and
raises `TimeoutError`. chatinho turns an exception into the result
`ws_run failed: <Type>: <message>`, so a refusal is an error the agent sees.
Paths outside a workspace are refused by chatinho's `Tree` and
`WorkspaceBackend`. The shell is not a sandbox: a command can still reach the
machine, and the push refusal is a pattern on the command text.
(add-chatinho-harness)

### /merge is ours and only the user's

`MergeCommand(provider, backend)` refuses, in order and changing nothing: a
model (`only the user can merge: ask the user to run /merge <name>`), no name,
a run with no change yet (`the run has no change yet: ask the peer working on
the change to go on with it (such as @build go on with <change>), then merge`;
taking the change the worktree's branch changed was rejected
(harness-chat-only)), a name that is not a worktree, and a worktree with
uncommitted changes (they would be left behind when it is removed). Otherwise
it calls `merge_branch` (workflow) for `peer/<name>` in the main checkout for
the run's change, then drops the worktree and its branch; a
`BranchMergeError` becomes an error reply naming its files and the worktree
stays. chatinho's `/ws merge` was rejected: it aborts on the `tasks.md`
conflict both implement halves make. (add-chatinho-harness)

### The chat opens empty; nothing is said for the user

`run_harness(ws)` builds a plain chatinho `ChatSession` and opens it with no
message: the user starts or continues a change by messaging a peer. Taking a
request (or a `--change`) and saying it to the peer of the change's phase was
rejected as a second way to do what the chat already does. A run never loads
an earlier conversation. (harness-chat-only)

### The conversation lives in the run's change folder

`GitBackend` appends each message as one JSON line (`id`, `from`, `to`,
`replyTo`, `status`, `text`, `at`; never credentials) to a git-ignored
`chat.jsonl` in the folder of the run's change. (add-chatinho-harness) The
run's change is found from what the run does: at start the backend snapshots
each active change's `signature` (the newest `st_mtime_ns` of any file in its
folder except `chat.jsonl`, `events.jsonl`, `events.sent` and `.gitignore`);
lines are held in memory until, after a message, an active change is new or
its signature differs, and the first by name becomes the run's change and gets
the held lines. The backend's own log and the telemetry log (with the
`.gitignore` its first event creates) are left out, so a peer that only checks
another change (`gate`, `validate`, `run`) never binds it. Binding to the
change a peer names in a message was rejected: a peer may name a change it
only reads. (harness-chat-only) The folder's `.gitignore` gains `chat.jsonl`
through `ensure_ignored` (project). A write failure is logged and ignored.
(add-chatinho-harness)

### The model comes from the environment, or from a Copilot login

`model_from_env` builds `ChatOpenAI` from `SPECWORKS_MODEL_API_KEY`,
`SPECWORKS_MODEL_MODEL` and the optional `SPECWORKS_MODEL_BASE_URL`; a missing
one raises `ModelSettingsError` naming the variable, never a value, and for
the key saying to run `specworks login copilot`. (add-chatinho-harness,
add-copilot-login) When the key is missing or empty, it uses the stored Copilot
login of the project (local before global) instead; an explicit key makes no
stored-login read and no request. (add-copilot-login)

### The Copilot login lives in the harness and outside the project

`copilot.py` (device flow, token exchange, `log_in`) and `logins.py` (the
stored login) sit here because only the harness uses them and they share its
extra; `integrations` must stay free of the extra. Only the long-lived OAuth
token is stored, in the user's config dir (`$XDG_CONFIG_HOME` or `~/.config`,
`%APPDATA%` on Windows) under `specworks/copilot/`: `global.json`, and
`projects/<sha256 of the project root path, 16 hex>.json` for a local login.
Folders are 0700 and files 0600, written by rename so a failed write keeps the
earlier login. A local login is never kept inside the project, because a
peer's file tools read its checkout (inside `.specworks/` was rejected, and
the OS keychain for its per-OS dependency). Moving a project loses its local
login. (add-copilot-login)

### The session token is a callable key, exchanged with sync `httpx`

The key given to `ChatOpenAI` is `CopilotSession.token`, a sync callable that
returns the cached session token and exchanges a new one 60 seconds before it
expires (a lock keeps two threads from exchanging at once); a sync callable
serves both of the model's clients, where the source's async provider failed
the sync one. The first exchange runs when the model is built, giving the API
base (`endpoints.api`, else `https://api.githubcopilot.com`) and an early
error for a login GitHub no longer accepts. The session token is never stored,
and no error, repr or log carries a token. (add-copilot-login)

### Logging in reuses a working login

`log_in` loads the scope's login and, unless forced, tries one exchange:
success is a reuse and nothing is written; a rejected token (401/403) starts
the device flow; a network error is an error. The device flow does not open a
browser: it calls `prompt(uri, code)` (stderr in the CLI), polls at GitHub's
interval (+5 s on `slow_down`) and fails on denial, expiry or its deadline,
leaving the earlier login as it was. A login stored for one GitHub host is
reused for another unless `--force` is given. (add-copilot-login)

## Interfaces

- `specworks.harness`: `build_harness`, `run_harness`, `model_from_env`,
  `ModelSettingsError`.
- `session.py`: `build_harness(ws, model, *, frontend=None) -> ChatSession`
  (`workspaces=SpecworksWorktrees(ws, worktree_peers(PEERS))`, commands `/ws` and `/merge`;
  `frontend=None` builds the terminal); `run_harness(ws)`.
- `peers/base.py` (re-exported by `peers`): `PREFIX`, `PREAMBLE`,
  `MERGE_RULE`, `MEMORY`, `peer_name(skill)`, `preamble(name, peers,
  rules=())`, `skill_instructions(skill, peers, rules=())`;
  `SkillPeer(model, peers)` with class attributes `name`,
  `worktree: ClassVar[bool] = False`, `rules: ClassVar[tuple[str, ...]] = ()`,
  classmethod `skill_name()`, `skill`, `answer()`, `listen()`,
  `hand_over_tool()` (agent tool `hand_over(peer, text)` -> `handed over to
  <peer>` or `error: unknown peer '<peer>'` / `error: cannot hand over to
  yourself`).
- `peers/<name>.py`: `<Name>Peer(SkillPeer)` for each of the 15 skills
  (`BuildPeer.rules = (MERGE_RULE,)`, `TestPeer.worktree = True`).
- `peers/__init__.py`: `PEERS: tuple[type[SkillPeer], ...]`,
  `worktree_peers(peers=PEERS) -> frozenset[str]`.
- `workspaces.py`: `RUN_TIMEOUT`, `WorkspaceError`
  (`files`); `SpecworksWorkspace.run(command) -> str` (`ws_run`);
  `SpecworksWorktrees(ws, worktrees=None)` (`None`: `worktree_peers()`) with
  `worktrees`, `provision(owner, name, create=True)` and
  `current_branch()`; `MergeCommand(provider, backend)` (`/merge <name>`, user
  only).
- `confine.py`: `PUSH_RE`, `HIDDEN_ENV`, `refuses(command)`,
  `shell_env(env=None)`.
- `backend.py`: `CHAT_FILE` (`chat.jsonl`), `signature(folder) -> int` (`0`
  for an empty or unreadable folder); `GitBackend(ws, module)` with `change`
  (`None` until the run's change is found), `listen`, `forget` (drops held
  lines only), `to_line(msg)`.
- `model.py`: `MODEL_KEY`, `MODEL_NAME`, `MODEL_BASE_URL`,
  `ModelSettingsError(variable)`,
  `model_from_env(env=None, *, root=None, store=None, client=None)`;
  `run_harness(ws)` passes `root=ws.root`.
- `logins.py`: `Scope` (`"global"` or `"local"`), `Login(oauth_token, ghe_host="")`
  (token hidden from `repr`), `config_dir(env=None) -> Path`,
  `LoginStore(base=None)` with `save(scope, root, login)`, `load(scope, root)`
  and `find(root)` (local, then global).
- `copilot.py`: `EDITOR_HEADERS`, `CopilotLoginError(message, *, login_again=False)`,
  `CopilotSession(login, *, client=None, now=time.time)` with `token()` and
  `api_base`, `device_login(ghe_host, prompt, *, client, sleep, now) -> Login`,
  `LoginResult(scope, reused)`, `log_in(scope, root, *, force, ghe_host, prompt,
  store, client, sleep, now) -> LoginResult`.

## Constraints

- Imported only from the `harness` command's body; `import specworks` and
  every other command never load chatinho or deepagents.
- The `harness` extra (specworks requires Python 3.12+; chatinho pinned to a commit with its
  `tui` and `deepagents` extras, `deepagents>=0.7.34,<0.8`); tests in
  `tests/harness/` skip without it and use a scripted chat model (no network);
  every CI job installs it and covers the package. (require-python-3-12)
- No peer pushes or merges a worktree; refusals are errors the agent sees,
  never crashes of the run.
