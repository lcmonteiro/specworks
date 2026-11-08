# Design: harness-chat-only

## Context

See proposal.md. Today `specworks harness [REQUEST] [--change REF]`
(`src/specworks/cli/harness.py`) resolves `--change`, and `run_harness` →
`build_harness` builds a `HarnessSession` (`src/specworks/harness/session.py`)
whose `start()` says the request to `first_peer(change)`. `GitBackend`
(`src/specworks/harness/backend.py`) takes the change, or else notes the
active change names at start and binds to the first *new* one; its `load()`
gives back the change's `chat.jsonl`.

## Goals / Non-Goals

**Goals:**
- `specworks harness` with no argument or option; an empty chat every time.
- The run's change found from what the run does, new change or existing.

**Non-Goals:**
- Choosing an earlier conversation to load.

## Decisions

### The command and the session lose their inputs

`harness()` takes no parameter and calls `run_harness(ws)`. `build_harness(ws,
model, *, frontend=None)` builds a plain chatinho `ChatSession` directly, as
today (`build_chat_session` takes no `workspaces`); `HarnessSession` and
`first_peer` are removed, since nothing is said for the user.
Serves: REQ-CLI-022.

### The run's change is the first active change whose folder changes

`GitBackend(ws, module)` takes a snapshot at start: for each active change, a
signature of its folder, the newest modification time (`st_mtime_ns`) of any
file in it except `chat.jsonl`. After each message it heard, while it has no
change, it compares the active changes with the snapshot and binds to the first
one, by name, that is new or whose signature differs; then it writes the held
lines. `chat.jsonl` is left out of the signature so the backend's own writes
never count. `HookLoad` is no longer declared (no reload); `from_line` stays
for reading a log in tests.
Serves: REQ-HARNESS-009.

Alternative: bind to the change a peer names in a message. Rejected: it needs
parsing the text, and a peer may name a change it only reads.

## Interfaces

Agreed with the user (with one change: `build_harness` builds `ChatSession(...)` directly, as today, not through `build_chat_session`, which takes no `workspaces`)

- `src/specworks/cli/harness.py`: `harness() -> None` (no argument, no option) (REQ-CLI-022)
- `src/specworks/harness/session.py`: `build_harness(ws: Workspace, model: BaseChatModel, *, frontend: Any = None) -> ChatSession`; `run_harness(ws: Workspace) -> None`. Removed: `first_peer`, `HarnessSession` (REQ-CLI-022)
- `src/specworks/harness/backend.py`: `GitBackend.__init__(self, ws: Workspace, module: Module)` (**BREAKING**: the `change` parameter goes); `GitBackend.change: Change | None` kept, `None` until the run's change is found (`MergeCommand` reads it; its tests set it directly); `signature(folder: Path) -> int`, the newest `st_mtime_ns` of any file in `folder` except `chat.jsonl`, `0` for an empty or unreadable folder; `HookLoad` and `load()` removed (REQ-HARNESS-009)
- `src/specworks/harness/__init__.py`: exports unchanged (`build_harness`, `run_harness`, `model_from_env`, `ModelSettingsError`)

## Diagrams

No structural change.

## Risks / Trade-offs

- [Two changes touched in the same message] -> the first by name wins; the
  flow works on one change at a time.
- [A file timestamp unchanged by an edit on a coarse filesystem] -> any later
  write in the folder binds it; held lines are written then, in order.

## Migration / Rollback

None: a stopped run is continued by opening the chat and messaging a peer.

## Open Questions

None.
