# Design: add-chatinho-harness

## Context

Reopened (see proposal.md and refinement.md): the harness moves from chatinho
`d3f29a2` to `c7bcc17` and onto what chatinho now ships.

chatinho `c7bcc17` (Python >= 3.12) gives, besides the session, terminal,
commands and backends the harness already uses:
- `DeepAgentConnector(name, model, tools=(), *, workspace=True,
  agent_memory=None, **options)` (`chatinho.connectors.deep`, extra
  `deepagents`): an `AgentConnector` whose agent is `create_deep_agent`'s.
  With a workspace provider its backend is `/` = its own workspace and
  `/peers/<name>/` = each other workspace, read-only; its `system_prompt` is
  kept after a "where things are" paragraph; a `backend` option is refused. It
  gets `ws_<op>` tools for the workspace operations its file tools do not
  cover.
- `GitWorktrees(repo, base=None, view=WorkspaceView, workspace=Workspace)`
  (`chatinho.workspaces`): the provider, given as `ChatSession(workspaces=...)`.
  `provision(owner, name, create=True)` returns `name`'s workspace, writable
  when `owner == name`. Worktrees live at `.chatinho/worktrees/<name>` on
  `peer/<name>`, kept out of `git status` through `info/exclude`; `base` is
  fixed at `initialize()` to the branch then checked out unless given.
  `merge(name)` aborts on a conflict (`MergeConflict`).
- `WorkspaceView` / `Workspace` with operations declared by
  `@operation(description, writes=...)` on async methods; a subclass adds
  operations and every consumer picks them up. Paths outside a workspace raise
  `ValueError`, which `WorkspaceBackend` turns into error results.
- `WorkspaceCommand` (`/ws`): list, diff, and merge / drop for the user only.

Specworks pieces kept: `read_skill`, `merge_branch` (REQ-FLOW-015),
`GitBackend` and `chat.jsonl`, `model_from_env`, the CLI command, the hand-over
said from a fresh context after the run.

## Goals / Non-Goals

**Goals:**
- Delete what chatinho now provides: the `graph()` override, `Workspaces`,
  `/workspace`, `ConfinedShell`, `PeerShell`.
- Keep every user-facing outcome; the only new stop is the user's
  `/merge test`.
- Fix the Windows failure of the test of AC-HARNESS-008.2.

**Non-Goals:**
- A sandbox; any chatinho change; worktrees for peers other than `test`.

## Decisions

### SkillPeer is a thin DeepAgentConnector

`SkillPeer(DeepAgentConnector)` passes `system_prompt=skill_instructions(...)`,
`ask_user=True`, the chat memory and `tools=[hand_over]`; it overrides only
`answer()` (the run, then the recorded hand-over said from a fresh context, as
before) and `listen()` (does nothing). The model and the backend come from
chatinho. Serves: REQ-HARNESS-002, REQ-HARNESS-003, REQ-HARNESS-005.

Alternative: keep `SkillPeer(AgentConnector)` with our `graph()` override.
Rejected: it copies what chatinho now owns and cannot use its workspaces.

### The preamble gains the merge rule

**Pinned wording** (`src/specworks/harness/peers.py`, verbatim; `{peers}` is
the names joined by `, `):

```
You are the peer `{name}` in a specworks harness chat. The other peers are: {peers}.
No one types slash commands here: `/specworks-<name>` in your skill means the peer `<name>`.
When your skill stops with a question that only offers the next step, take the option marked (recommended) and call hand_over with that peer and the change ref; do not ask the user.
When your skill asks the user anything else, call ask_user and wait for the answer.
When the recommended option is `stop here`, end without calling hand_over.
When your skill merges a worktree's branch, do not merge it yourself: call ask_user asking the user to run `/merge <name>`, and wait.
```

Serves: REQ-HARNESS-004.

### SpecworksWorktrees: one shared checkout, one test worktree

`SpecworksWorktrees(GitWorktrees)` is built with `repo=ws.root`,
`workspace=SpecworksWorkspace`. `WORKTREE_PEERS = frozenset({"test"})`.
`provision(owner, name, create)`:
- `name` not in `WORKTREE_PEERS`: the main checkout, as one chatinho `Tree`
  for the whole provider (one lock), built after `initialize()` with
  `Tree(top, "checkout", <current branch>, "HEAD", WorkspaceView, <the
  provider's identity>)`: its base is `HEAD`, so its `diff` is the uncommitted
  work and stays right when a skill switches the checkout's branch. It is a
  `SpecworksWorkspace` when `owner` is also a checkout peer, a `WorkspaceView`
  otherwise (another peer, `test`, or `None` for a command);
- `name` in `WORKTREE_PEERS`: before chatinho creates a worktree that does not
  exist yet, `base` is set to the branch the checkout has now (`git
  symbolic-ref --short HEAD`, else `HEAD`'s commit); then chatinho's
  `provision`.
`/ws` lists `names()`, which are only real worktrees (`test`).
Serves: REQ-HARNESS-006, REQ-HARNESS-008.

Alternative: one worktree per peer, chatinho's default. Rejected with the
refinement: every stage would need a merge.

### run is a workspace operation

`SpecworksWorkspace(Workspace)` adds
`@operation("Run a shell command in the workspace and return its output and exit code", writes=True) async def run(self, command: str) -> str`.
It refuses `refuses(command)` with
`PermissionError("git push is refused: only the user pushes")` before starting
anything; otherwise it starts the command through the platform shell
(`asyncio.create_subprocess_shell`, stderr merged into stdout) with
`cwd=self.tree.root` and `env=shell_env()`, waits up to the module's
`RUN_TIMEOUT` (600 s, read at call time so a test can shorten it) and then
kills it and waits for it to exit, raising
`TimeoutError("command stopped after <RUN_TIMEOUT> seconds")`; it returns
`"exit code <n>\n<output>"`. `writes=True` serialises it with the workspace's
other writes. Agents get it as `ws_run`; chatinho's tool turns an exception
into the result `ws_run failed: <Type>: <message>`, the error the agent sees.
`confine.py` keeps `PUSH_RE`, `HIDDEN_ENV`, `refuses` and `shell_env`;
`shell_env(env)` filters `env` (default `os.environ`).
Serves: REQ-HARNESS-008, REQ-HARNESS-010.

### /merge stays ours, user only

`MergeCommand(provider, backend)` (the specworks workspace and module are the
backend's `ws` and `module`, as before). Every refusal is an error reply and
changes nothing, checked in this order:
- `by != LOCAL`: `only the user can merge: ask the user to run /merge <name>`;
- no name: `usage: /merge <name>`;
- `backend.change is None`: `the run has no change yet: create it before
  merging a workspace`;
- a name not in `await provider.names()`: `no workspace '<name>'`;
- uncommitted changes in the worktree: `workspace '<name>' has uncommitted
  changes: commit them in it before merging` (the guard accepted in R5, kept so
  the removal below never loses work).
Otherwise `merge_branch(backend.ws, backend.module, change, "peer/<name>")` in
the checkout, then `await provider.drop(name)` (worktree and branch removed);
the reply lists `resolved <file>` lines, `merged peer/<name> into the main
checkout` (or `already up to date`) and `workspace <name> removed`. A
`BranchMergeError` becomes an error reply naming its files; the worktree
stays. Serves: REQ-HARNESS-007.

Alternative: chatinho's `/ws merge`. Rejected: it aborts on the `tasks.md`
conflict both halves make.

### The Windows-safe test of AC-HARNESS-008.2

The test runs `ws_run` with `"<python>" -c "import os; print(os.getcwd())"`
(the test's own interpreter) and compares `Path(output).resolve()` with the
worktree's resolved path. Serves: REQ-HARNESS-008.

### Packaging

- `pyproject.toml`: `harness = ["chatinho[tui,deepagents] @ git+https://github.com/lcmonteiro/chatinho@c7bcc176c633d9aab17c4cb4874dbc40aae4ef85 ; python_version >= '3.12'", "deepagents>=0.7.34,<0.8 ; python_version >= '3.12'"]`,
  the same in the dev group; `uv.lock` regenerated.
- Kept as before: mypy override, `tests/harness/conftest.py` skip, scripted
  model, CI coverage split.

Unchanged decisions (hand-over from a fresh context, `GitBackend`,
`ensure_ignored`, `model_from_env`, the lazy CLI) are as closed; see the living
`src/specworks/harness/docs/design.md`.

## Interfaces

Agreed with the user

- `src/specworks/harness/peers.py`:
  - `PREAMBLE: str` (the pinned wording above) (REQ-HARNESS-004)
  - `class SkillPeer(DeepAgentConnector)`: `__init__(self, skill: str, model: BaseChatModel, peers: Sequence[str])`; `skill: str`; `async answer(msg: ChatMessage) -> Reply`; `async listen(msg: ChatMessage) -> None`; `hand_over_tool() -> StructuredTool` (unchanged results) (REQ-HARNESS-002, REQ-HARNESS-003, REQ-HARNESS-005). `graph()` and `shell` are removed.
  - `peer_name`, `preamble`, `skill_instructions`: unchanged (REQ-HARNESS-001, REQ-HARNESS-004)
- `src/specworks/harness/workspaces.py`:
  - `WORKTREE_PEERS: frozenset[str] = frozenset({"test"})`; `RUN_TIMEOUT: float = 600.0` (REQ-HARNESS-006, REQ-HARNESS-008)
  - `class SpecworksWorkspace(chatinho.workspaces.Workspace)`: `async run(self, command: str) -> str` (`@operation(..., writes=True)`), returns `"exit code <n>\n<output>"`, raises `PermissionError` (a push) and `TimeoutError` (past `RUN_TIMEOUT`) (REQ-HARNESS-008)
  - `class SpecworksWorktrees(GitWorktrees)`: `__init__(self, ws: specworks.core.workspace.Workspace)` (`repo=ws.root`, `workspace=SpecworksWorkspace`); `async provision(self, owner: str | None, name: str, create: bool = True) -> WorkspaceView`; `async current_branch() -> str` (REQ-HARNESS-006)
  - `class MergeCommand` (`@tool("merge", "Merge a workspace into the main checkout: /merge <name>")`, `@require(HookExecute)`): `__init__(self, provider: SpecworksWorktrees, backend: GitBackend)`; `async execute(args: str = "", by: int = LOCAL, **kwargs: Any) -> Reply`, every refusal an error reply with the messages of the Decision above (REQ-HARNESS-007)
  - Removed: `Workspaces`, `WorkspaceCommand` (specworks' `/workspace`), `WORKSPACES_DIR`, `MAIN`, `NAME_RE`. `WorkspaceError(SpecworksError)` with `files` is kept for `/merge`.
- `src/specworks/harness/confine.py`: `PUSH_RE`, `refuses(command: str) -> bool`, `shell_env(env: Mapping[str, str] | None = None) -> dict[str, str]` (REQ-HARNESS-008, REQ-HARNESS-010). `HIDDEN_ENV` kept. Removed: `ConfinedShell`, `confined`, `PeerShell`, `OutsideWorkspaceError` (chatinho's `Tree.resolve` and `WorkspaceBackend` now refuse outside paths).
- `src/specworks/harness/session.py`: `build_harness(...)` signature unchanged; it builds the session with `workspaces=SpecworksWorktrees(ws)` and the commands `/ws` (chatinho's `WorkspaceCommand`) and `/merge` (REQ-HARNESS-006, REQ-HARNESS-007)
- Unchanged: `src/specworks/harness/model.py`, `src/specworks/harness/backend.py`, `src/specworks/cli/harness.py`, `src/specworks/core/events.py`.

## Diagrams

![The harness after the change (REQ-HARNESS-002, REQ-HARNESS-006, REQ-HARNESS-007)](diagrams/harness-blocks.svg)

![The cli after the change (REQ-CLI-022)](diagrams/cli-blocks.svg)

![A hand-over between stages (REQ-HARNESS-003)](diagrams/hand-over-flow.svg)

## Risks / Trade-offs

- [Overriding `GitWorktrees.provision` and building a `Tree` for the checkout
  relies on chatinho internals] -> pinned commit; AC-HARNESS-006.x exercise it.
- [`run` serialises with the checkout's writes, so a long test run delays
  another phase peer's write] -> the phases are sequential; only `test` works in
  parallel, in its own worktree.
- [chatinho's `/ws merge test` is still there and aborts on `tasks.md`] -> the
  preamble sends peers to `/merge`; a failed `/ws merge` changes nothing.
- [The shell can still reach the machine] -> out of scope, as before.

## Migration / Rollback

Existing `.specworks/workspaces/` worktrees from the closed version are not
read any more; remove them with `git worktree remove`.

## Open Questions

None.
