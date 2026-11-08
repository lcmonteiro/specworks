# Refinement: add-chatinho-harness

## Problem

The change was closed with its own Deep Agent peer, worktrees, merge command
and confined shell, built on chatinho `d3f29a2`. Since then chatinho's `main`
(`c7bcc17`, PR #51) ships the same concepts itself: `DeepAgentConnector`, a
workspace provider of git worktrees with the `/ws` command, and
`WorkspaceBackend`, which hands a workspace to a deep agent. Keeping our copies
means maintaining code chatinho now owns, and working around its rules (only
the user merges). The closed version also fails CI on Windows: the test of
AC-HARNESS-008.2 compares `pwd` text (`/c/Users/...` from Git Bash) with a
Windows path. Reopened by the user to update chatinho and rebuild on it.

## Outcomes

- `specworks harness "<request>"` still opens a chatinho terminal with the user
  and one peer per skill; `@<peer> <text>` still talks to any peer.
- The run still moves `refine → specify → build → done` on its own and stops
  where a skill asks the user, and now also when `build` needs the test half
  merged: the user approves it in the chat with `/merge test`; a model asking
  for it is refused.
- The phase peers work in the user's checkout on the change's branch, so each
  stage sees the previous one's files and the run ends with a closed change on
  that branch, nothing left to merge.
- The test half works in its own worktree; anyone can list and diff the
  worktrees with `/ws`, and peers read each other's work under `/peers/<name>/`.
- A stopped run continues its conversation; the model and its errors are as
  before (`SPECWORKS_MODEL_*`, never a key shown); without the extra the
  command says what to install.
- CI passes on every job, Windows included.

## Context

**Observed (chatinho `c7bcc17`):**
- `DeepAgentConnector` (`connectors/deep.py`): built from `create_deep_agent`'s
  options, the same chat behaviour as `AgentConnector` (`ask_<peer>`,
  `run_<command>`, `ask_user`, error replies), `system_prompt` kept after a
  short "where things are" paragraph; a `backend` option is refused, because
  the workspace is the backend.
- `GitWorktrees` (`workspaces/git.py`), given as `ChatSession(workspaces=...)`:
  not a peer; `provision(owner, name)` returns `name`'s workspace, writable
  when `owner == name`; one worktree per peer at `.chatinho/worktrees/<name>`
  on `peer/<name>` from a base fixed when it starts; `merge` aborts on a
  conflict.
- `/ws` lists, diffs, merges and drops; `merge` and `drop` only for the user
  (`by == LOCAL`).
- Workspace operations are declared methods (`ls`, `read`, `glob`, `grep`,
  `diff`, `log`, `write`, `edit`, `delete`, `commit`); a project adds its own by
  subclassing, and each becomes a `ws_<op>` tool. `WorkspaceBackend` is not a
  sandbox backend: there is no shell.
- chatinho's `deepagents` extra (`deepagents>=0.7.34,<0.8`).

**Observed (specworks):** the living `harness` spec
(`src/specworks/harness/docs/`, REQ-HARNESS-001..010) and its code
(`peers.py`, `workspaces.py`, `confine.py`, `backend.py`, `session.py`,
`model.py`); `specworks merge` (REQ-FLOW-015) keeps both halves' ticks in
`tasks.md`; skills run `specworks new` (creates and switches the change branch)
and `specworks commit` in the checkout.

**Assumed:** subclassing `GitWorktrees` (overriding `provision` and the base) is
a supported extension point, as chatinho's operations are.

## Constraints

- [hard] Skills unchanged; peers are Deep Agents; keys only from
  `SPECWORKS_MODEL_*`; core stays on 3.11, the harness on 3.12+ behind
  `specworks[harness]`; scripted model in tests only; no peer pushes.
- [hard] chatinho pinned to a commit of its `main` (`c7bcc17` or later); no
  chatinho change.
- [hard] Only the user merges, as chatinho's `/ws merge` rules.
- [soft] Delete our code that chatinho now provides rather than keep both.
- [soft] 95% branch coverage, measured for the harness on 3.12+.

## Options

### Option A: Shared worktrees on chatinho's workspaces (chosen)

Peers are `DeepAgentConnector`s (skill as `system_prompt`, after the
preamble). A specworks `GitWorktrees` subclass maps the phase peers onto the
main checkout (base following its current branch) and `test` onto its own
worktree. A `run` operation on a workspace subclass gives agents `ws_run`, with
the push refusal and key stripping. A user-only `/merge test` runs
`specworks merge`. `GitBackend` and the model stay.

- **Pros:** most of `peers.py`, `workspaces.py` and `confine.py` go; chatinho's
  rules kept; stages share files with no merging; `/ws` for free.
- **Cons:** one more user stop (the test merge); relies on subclassing
  `GitWorktrees`.
- **Effort:** M
- **Touches:** `harness` (modified); `cli` only if the command changes.
- **Outcomes:** meets all.

### Option B: chatinho's workspaces as they are

One worktree per peer; the user `/ws merge`s after every stage.

- **Pros:** no customisation.
- **Cons:** the run no longer moves on by itself; `tasks.md` conflicts abort
  chatinho's merge.
- **Effort:** S
- **Outcomes:** fails "moves on its own" and "nothing left to merge".

### Option C: Only `DeepAgentConnector`

Keep our worktrees, `/merge` and shell; adopt only the connector.

- **Pros:** the smallest change.
- **Cons:** keeps code chatinho now owns; the connector refuses a `backend`, so
  our shell needs a workaround; models still merge.
- **Effort:** S
- **Outcomes:** meets the user-facing outcomes, fails "only the user merges".

## Recommendation

Option A, agreed with the user, with the phase peers in the main checkout and
the test half merged by a user-only `/merge test` that runs `specworks merge`.

## Open Questions

- Must a peer commit before it hands over, or does the next stage pick up the
  uncommitted work in the shared checkout? (who can answer: the user, at
  specify)
- Does `ws_run` need a timeout for long commands? (who can answer: the user, at
  specify)

## Candidate Capabilities

- `harness`: modified - peers become `DeepAgentConnector`s; workspaces come from
  a specworks `GitWorktrees` subclass (shared checkout, test worktree), the
  shell from a `run` operation, the test merge from a user-only `/merge`;
  REQ-HARNESS-002, -006, -007 and -008 change; the test of AC-HARNESS-008.2 is
  fixed for Windows.
- `cli`: unchanged unless specify finds the command's surface moves.
