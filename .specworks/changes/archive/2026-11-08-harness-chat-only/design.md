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
file in it except `chat.jsonl`, `events.jsonl` and `events.sent`. After each
message it heard, while it has no change, it compares the active changes with
the snapshot and binds to the first one, by name, that is new or whose
signature differs; then it writes the held lines. `chat.jsonl` is left out so
the backend's own writes never count; the telemetry log (`events.jsonl`,
`events.sent`, `core.events` `EVENTS_FILE` and `SENT_FILE`) is left out
because every change command appends to it, read-only ones included (`gate`,
`validate`, `cycle`, `run`): a peer that only checks another active change
must not make it the run's, so only a peer's own work on a change binds it
(review R1). The folder's `.gitignore` (`core.events` `IGNORE_FILE`) is left
out too: `record_event` creates or extends it through `ensure_ignored` the
first time a change logs an event, so on a change with no event yet a
read-only check would still bind it; nothing but that side effect of a log
writes it during a run (review R4). `HookLoad` is no longer declared (no reload), and `from_line`
goes with `load()`, its only reader (review R2).
Serves: REQ-HARNESS-009.

### `/merge` before the run has a change says how to get one

A run now has no change until a peer works in a change folder, so on a run
that continues an existing change the user may run `/merge test` first.
`MergeCommand.execute` still refuses it with an error saying the run has no
change (AC-HARNESS-007.5), but the text no longer says to create one: it says
to ask the peer working on the change to go on first, so the run binds it, then
merge. The reply: `the run has no change yet: ask the peer working on the
change to go on with it (such as @build go on with <change>), then merge`
(review R3). No interface changes: only the refusal's text.
Serves: REQ-HARNESS-007 (AC-HARNESS-007.5).

Alternative: with no change yet, `/merge` takes the change whose folder the
worktree's branch changed. Rejected in review: it needs a spec change, and
the refusal already gives the user a way on.

Alternative: bind to the change a peer names in a message. Rejected: it needs
parsing the text, and a peer may name a change it only reads.

## Interfaces

Agreed with the user (cycle 3: the review decision on R4; cycle 2: the review decisions on R1, R2 and R3; cycle 1 with one change: `build_harness` builds `ChatSession(...)` directly, as today, not through `build_chat_session`, which takes no `workspaces`)

- `src/specworks/cli/harness.py`: `harness() -> None` (no argument, no option) (REQ-CLI-022)
- `src/specworks/harness/session.py`: `build_harness(ws: Workspace, model: BaseChatModel, *, frontend: Any = None) -> ChatSession`; `run_harness(ws: Workspace) -> None`. Removed: `first_peer`, `HarnessSession` (REQ-CLI-022)
- `src/specworks/harness/backend.py`: `GitBackend.__init__(self, ws: Workspace, module: Module)` (**BREAKING**: the `change` parameter goes); `GitBackend.change: Change | None` kept, `None` until the run's change is found (`MergeCommand` reads it; its tests set it directly); `signature(folder: Path) -> int`, the newest `st_mtime_ns` of any file in `folder` except `chat.jsonl`, `events.jsonl`, `events.sent` and `.gitignore`, `0` for an empty or unreadable folder (review R1, R4); `HookLoad`, `load()` and `from_line()` removed (review R2) (REQ-HARNESS-009)
- `src/specworks/harness/workspaces.py`: `MergeCommand.execute(self, args: str = "", by: int = LOCAL, **kwargs: Any) -> Reply` unchanged; with no change yet its error reply reads `the run has no change yet: ask the peer working on the change to go on with it (such as @build go on with <change>), then merge` (review R3) (REQ-HARNESS-007)
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
