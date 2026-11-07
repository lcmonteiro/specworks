# Proposal: add-chatinho-harness

## Why

The specworks flow runs only inside an AI coding tool, one `/specworks-*`
command typed at a time. Following the refinement's option A, this change adds
a harness that runs the whole flow as a chatinho chat: every skill is a
LangChain Deep Agent peer, the peers hand work to each other by message, and the
repository is the backend that keeps the conversation and the git workspaces.

## What Changes

- New `specworks harness [REQUEST] [--change REF]` opens a chatinho terminal.
  The user is peer zero; every packaged skill is a peer named after it without
  the `specworks-` prefix (`refine`, `specify`, `build`, `test`, ...); a git
  backend keeps the conversation. A request is handed to `refine`.
- Each skill peer is a Deep Agent (`create_deep_agent`) whose instructions are
  the packaged skill as `read_skill` returns it (unchanged), after a short
  harness preamble: take the skill's recommended next step and hand over to
  that peer; stop for the user only where the skill asks something else.
- A peer's tools: `hand_over(peer, text)` (a say addressed to the next peer,
  replying to the message it was working on, so stages never nest),
  `ask_<peer>` (ask and wait, used by `build` and `done` for their phases),
  `ask_user`, the `/workspace` and `/merge` commands, and file and shell tools
  rooted in its current workspace. A path outside it is refused, and `git push`
  is refused.
- `/workspace <name>` creates (or reuses) a git worktree on its own branch from
  the change's branch and makes it the invoking peer's workspace;
  `/workspace main` goes back to the main checkout. `/merge <name>` merges the
  workspace's branch into the main checkout as `specworks merge` does: on a
  conflict the merge is aborted, the checkout is left as it was and the
  conflicting files go back to the peer that asked; on success the workspace
  is removed.
- The backend appends every message to a git-ignored `chat.jsonl` in the
  change's folder and loads it at start, so `specworks harness --change REF`
  continues a stopped run. Before the run has created its change, messages are
  held in memory and written to the change's folder once it exists.
- The model comes from `SPECWORKS_MODEL_API_KEY`, `SPECWORKS_MODEL_BASE_URL`
  (optional) and `SPECWORKS_MODEL_MODEL`; a missing one stops the command naming
  the variable, never a value.
- Packaging: a `harness` extra (chatinho with its `tui` and `langchain`
  batteries, and `deepagents`), Python 3.12+ only. `import specworks` and every
  other command never import it; `specworks harness` without it says which
  extra to install. CI's coverage job moves to 3.12+ with the extra; the 3.11
  job skips `tests/harness`.
- A change's `.gitignore` now gains the names it lacks instead of being written
  only when missing, so `chat.jsonl` and `events.jsonl` are both ignored
  whichever came first.

## Capabilities

### New Capabilities

- `harness` ((top), `src/specworks/harness`): runs the specworks flow as a
  chatinho session: one Deep Agent peer per skill, handing over by message,
  confined to git workspaces that a git backend creates and merges, with the
  conversation kept in the change's folder and the model read from the
  environment.

### Modified Capabilities

- `cli`: adds REQ-CLI-022 `harness` (the command, its errors without the extra
  or a key).
- `project`: REQ-PROJ-030 a change's `.gitignore` gains the names it lacks.

## Related requirements

- REQ-PROJ-030 modified: the change folder's `.gitignore` is shared with the
  harness's `chat.jsonl`, so missing names are added to an existing file.
- REQ-PROJ-014 left: command result reuse is not touched.
- REQ-PROJ-033 left: reopening moves the folder, `chat.jsonl` with it.
- REQ-INTEG-003 left: d2 is not touched.
- REQ-INTEG-007 left: the harness reads skills through `read_skill`, which
  fills includes as today.
- REQ-INTEG-008 left: Langfuse variables are unchanged; the model variables
  follow the same rule (values never shown) in their own requirement.
- REQ-INTEG-009 left: sending events is unchanged.
- REQ-CLI-004 left: `context` does not show the harness.
- REQ-CLI-010 left: `/merge` reuses the same merge; the command is unchanged.
- REQ-CLI-012 left: `commit` stages the change folder, and git skips the
  ignored `chat.jsonl`.
- REQ-CLI-017 left: the harness records no telemetry events of its own; the
  CLI commands its peers run record theirs as today.
- REQ-CLI-018 left: `telemetry push` is unchanged.
- REQ-SPECS-015 left: code tasks waiting on the test half are unchanged.

## Impact

- New package `src/specworks/harness` (peer, backend, workspaces, model,
  session builder); new command in `src/specworks/cli`; a small change in
  `src/specworks/core` (`.gitignore`).
- `pyproject.toml`: the `harness` extra (`chatinho` from git, pinned to a
  commit; `deepagents`), the dev group and mypy settings for a module that
  needs 3.12+.
- `.github/workflows/ci.yml`: coverage on 3.12+ with the extra; 3.11 skips
  `tests/harness`.
- New tests in `tests/harness/` with a scripted chat model (tests only, no
  network).
- No skill text changes.

## Out of Scope

- A headless mode or an automatic answer policy (the refinement chose the
  interactive chat).
- Approval prompts for writes outside a workspace: they are refused instead.
- Real sandboxing of the shell: commands run in the workspace with `git push`
  refused, but a command can still reach the rest of the machine.
- Telemetry events for harness messages.
- Moving `SkillPeer` or the git backend into chatinho.
- A runnable scripted model (`--model scripted`): the user chose tests only.
- Pushing: no peer pushes; the user pushes after the run.
