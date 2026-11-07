# Proposal: add-chatinho-harness

## Why

Reopened: chatinho's `main` (`c7bcc17`) now ships deep-agent peers
(`DeepAgentConnector`), git-worktree workspaces (`GitWorktrees`, `/ws`) and a
deep agents backend over a workspace (`WorkspaceBackend`), which the harness
had built for itself on `d3f29a2`. Following the refinement's option A, the
harness moves onto them, keeps chatinho's rule that only the user merges, and
fixes the Windows CI failure in the test of AC-HARNESS-008.2.

## What Changes

- chatinho is pinned to `c7bcc17` with its `tui` and `deepagents` extras; the
  harness's own `deepagents` pin follows chatinho's (`>=0.7.34,<0.8`).
- Each skill peer is a `DeepAgentConnector` (subclassed only to add
  `hand_over`, the preamble and doing nothing on unaddressed says). The
  override of `AgentConnector.graph()` goes.
- Workspaces come from a specworks `GitWorktrees` subclass: every phase peer's
  workspace is the main checkout (writable, shared), the `test` peer's is a
  worktree `peer/test` started from the checkout's current branch. Peers read
  each other's under `/peers/<name>/`; chatinho's `/ws` lists and diffs them.
  The `/workspace` command and `Workspaces` go.
- A `run(command)` operation on a specworks workspace class gives each peer a
  shell as `ws_run`: it runs in the workspace, refuses `git push`, drops the
  model and Langfuse keys from its environment, and stops a command after 600
  seconds. `ConfinedShell` and `PeerShell` go.
- `/merge <name>` runs `specworks merge` of that workspace's branch into the
  checkout for the run's change, only when the user runs it; a model is
  refused. After a merge the worktree and branch are removed. The preamble
  tells peers to ask the user for `/merge test` instead of merging.
- The test of AC-HARNESS-008.2 checks the shell's folder with a path the
  process reports, not `pwd` text, so it passes on Windows.
- Unchanged: one peer per skill, hand-over by message, `@peer`, `chat.jsonl`,
  the `SPECWORKS_MODEL_*` model, the `specworks harness` command.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `harness`: REQ-HARNESS-002 (a peer is a `DeepAgentConnector`, its tools),
  REQ-HARNESS-004 (the preamble's merge rule), REQ-HARNESS-006 (workspaces:
  shared checkout, the test worktree), REQ-HARNESS-007 (merging: user-only),
  REQ-HARNESS-008 (staying in the workspace: `ws_run`, read-only views, a
  timeout). REQ-HARNESS-001, -003, -005, -009 and -010 are kept as merged.
- `cli`: none beyond REQ-CLI-022 as merged (its delta is kept unchanged).
- `project`: none beyond REQ-PROJ-030 as merged (its delta is kept unchanged).

## Related requirements

- REQ-HARNESS-002, -004, -006, -007, -008 modified (this change's own IDs,
  updated in place at close).
- REQ-HARNESS-001, -003, -005, -009, -010 left: their behaviour does not change.
- REQ-CLI-022 left: the command's surface and errors do not change.
- REQ-PROJ-030 left: unchanged.
- REQ-FLOW-015 left: `/merge` calls the same merge.
- REQ-CLI-010 left: `specworks merge` is unchanged.
- REQ-INTEG-007 left: skills are still read through `read_skill`.
- REQ-INTEG-008 left: the Langfuse keys are dropped from the shell, as the
  model's are; their own rules are unchanged.

## Impact

- `src/specworks/harness/`: `peers.py` rebuilt on `DeepAgentConnector`;
  `workspaces.py` becomes the `GitWorktrees` subclass, the workspace class with
  `run`, and `MergeCommand`; `confine.py` reduced to the push and environment
  rules; `session.py` passes the provider and chatinho's `/ws`.
- `pyproject.toml` and `uv.lock`: chatinho at `c7bcc17` with `deepagents`.
- `tests/harness/`: updated to the new workspaces and tools; AC-HARNESS-008.2
  fixed for Windows.
- No skill text changes.

## Out of Scope

- Requiring a peer to commit before it hands over: the phase peers share one
  checkout, and the skills already commit after each phase.
- Any change to chatinho.
- A sandbox: `ws_run` runs on the machine, as before.
- More than one worktree besides the checkout: only `test` gets its own.
