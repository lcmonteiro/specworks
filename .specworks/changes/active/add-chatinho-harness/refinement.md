# Refinement: add-chatinho-harness

## Problem

Today the specworks flow runs only inside an AI coding tool (Claude Code or
Copilot) that reads the installed skills, and a person drives every step by
typing the next `/specworks-*` command. There is no way to run the whole flow
as a team of agents that hand work to each other on their own. chatinho
(https://github.com/lcmonteiro/chatinho), a chat library of peers that talk by
message, offers the design for such a harness: each skill becomes a peer, and
the repository becomes the backend that holds the context and the workspaces.

## Outcomes

- `specworks harness "<request>"` opens a chatinho terminal where the user is
  one peer and every specworks skill is another, named after it (`refine`,
  `specify`, `build`, `test`, ...).
- From a request, the run moves through `refine → specify → build → done` on
  its own: each peer takes its skill's recommended next step and hands over by
  message, and stops only where its skill asks the user something (a product
  decision, a confirmation to write).
- The user can talk to any peer at any time with `@<peer> <text>` (e.g.
  `@test add a case for an empty file`).
- Parallel work (build's test and code halves) happens in separate git
  workspaces that are merged back, and the run ends with a closed change on its
  branch, as the skills produce today.
- A stopped run reopened on the same change continues the conversation where
  it left off.
- The model is set with `SPECWORKS_MODEL_API_KEY` (plus `_BASE_URL`,
  `_MODEL`); a missing key stops the run naming the variable, never a value.
- `specworks harness` without the extra installed says which extra to install.

## Context

**Observed:**
- chatinho: everyone is a peer (`@connector`), with three verbs: `say`/`listen`
  (a message to everyone, or `to=` one peer), `ask`/`answer` (one peer, awaits
  the reply) and `invoke`/`execute` (commands). Replies point at a message with
  `reply_to`. The terminal routes `@name text` as a question to that peer.
  `ask` nests up to `max_depth` (8 in the builders).
- chatinho backend: a peer that declares `HookListen`/`HookLoad`/`HookForget`
  (plus `HookKeep`/`HookLink` for attachments); `DatabaseBackend` is the
  model. Connectors keep no state; they read the chat with `context()`.
- chatinho `AgentConnector` (`connectors/agent.py`) wraps LangChain's
  `create_agent` (not `create_deep_agent`) and turns the chat into tools
  (`ask_<peer>`, `run_<command>`, `ask_user`); other peers' says are only
  memory to it. `Endpoint.from_env(PREFIX)` reads `<PREFIX>_API_KEY`,
  `_BASE_URL`, `_MODEL`. `tests/fakes/agent.py` has a scripted
  `BaseChatModel` that calls no network.
- chatinho requires Python >= 3.12 and installs its batteries as extras
  (`tui`, `langchain`, ...); specworks requires >= 3.11 and CI tests 3.11-3.14.
- specworks: 15 skills as plain `SKILL.md` text in `src/specworks/skills/`
  (shared parts in `_shared/`). `/specworks-build` already runs its test half
  in its own git worktree; `/specworks-build` and `/specworks-done` run other
  skills in order. Capabilities `project` (changes, phases, commands, git),
  `integrations` (installs skills, telemetry), `cli` (command surface). The
  change folder already holds a git-ignored log (`events.jsonl`) and keys come
  only from `SPECWORKS_*` variables (`docs/architecture.md`).

**Assumed:**
- The `deepagents` package's `create_deep_agent` can load a packaged
  `SKILL.md` as its instructions and runs on the chat's event loop with async
  tools.
- A skill's text, followed by an agent, is enough to know its stops and its
  recommended next step; no skill needs a harness-specific hint.

## Constraints

- [hard] The current skills are not changed; the harness uses them as packaged.
- [hard] Peers are LangChain Deep Agents (`create_deep_agent`).
- [hard] The model key comes only from an environment variable, never from a
  file or the config; errors name the variable, never its value.
- [hard] The specworks core keeps Python 3.11; the harness needs 3.12+ and an
  optional extra (`specworks[harness]`), so `import specworks` never pulls
  chatinho, deepagents or langchain.
- [hard] Tests use a scripted model only, with no network; the scripted model
  does not ship.
- [hard] A peer never pushes (as the skills already say).
- [soft] Coverage stays at the project's 95% branch rule, measured for the
  harness on a 3.12+ job.
- [soft] Reuse chatinho as a dependency rather than copying it; no chatinho
  change is needed.

## Options

### Option A: Harness inside specworks

A `SkillPeer` chatinho connector builds one Deep Agent per skill, with its
`SKILL.md`, shell and file tools scoped to its workspace, and the chat as
tools. A `GitBackend` peer keeps the conversation in a git-ignored
`chat.jsonl` in the change folder (`HookListen`/`HookLoad`) and offers
`/workspace` (a git worktree on its own branch) and `/merge` as commands. A
handoff to the next stage is a `say` addressed to the next peer (`to=`,
`reply_to=`), so stages do not nest; `build` and `done` `ask` their sub-phase
peers and wait. `specworks harness` builds the session with the terminal.

- **Pros:** meets every outcome in this repo; skills used as-is; handoffs
  never hit `max_depth`; the backend follows chatinho's own backend shape.
- **Cons:** a new connector instead of reusing `AgentConnector`'s graph; a
  second Python floor (3.12) for one capability.
- **Effort:** L
- **Touches:** new `harness`; `cli` (the command); packaging and CI.
- **Outcomes:** meets all.

### Option B: Deep agents and the git backend in chatinho

chatinho's `AgentConnector` gains a deep-agent factory and chatinho ships the
git backend; specworks only wires them.

- **Pros:** reuses chatinho's agent graph (attachments, verify); others can use
  the backend.
- **Cons:** needs a chatinho change and release kept in step with specworks.
- **Effort:** L (across two repositories)
- **Touches:** chatinho; `cli`, packaging.
- **Outcomes:** meets all, once chatinho is released.

### Option C: A router peer drives the stages

A non-skill router listens for "stage done" messages and gives the next peer
its turn; skill peers never address each other.

- **Pros:** the least logic in the peers.
- **Cons:** the next step is decided outside the skills; the router must
  understand each skill's stops.
- **Effort:** M
- **Touches:** new `harness`; `cli`.
- **Outcomes:** fails "peers hand over by message"; moving on by default and
  stopping only where a skill asks are only partly met.

## Recommendation

Option A, agreed with the user: it is the only option that meets every outcome
within this repository and needs no chatinho release. `SkillPeer` and
`GitBackend` can move to chatinho later if they prove general.

## Open Questions

- Does a peer's write outside its workspace (or any command beyond the
  `specworks` CLI, tests and git) need the user's approval in the chat?
  (who can answer: the user)
- On a merge conflict between workspaces, does the backend report it to the
  peer that asked for the merge, or stop and ask the user? (who can answer:
  the user)
- Which CI job measures the harness's coverage, given the 3.11 job skips it?
  (who can answer: the user, at specify)

## Candidate Capabilities

- `harness`: new ((top), `src/specworks/harness`) - runs the specworks flow as
  a chatinho session: one Deep Agent peer per skill, a git backend that keeps
  the conversation and manages workspaces and merges, and the scripted-model
  test support.
- `cli`: modified - adds `specworks harness`, and its error when the extra is
  missing.
