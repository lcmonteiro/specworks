# Proposal: harness-chat-only

## Why

`specworks harness "<request>"` sends the request to `refine` (or to the peer of
the change's phase) as the user's first message. That is a second way to do
what the chat already does: typing `@refine <request>` starts a change. The user
asked for one way only: opening the harness opens the chat.

## What Changes

- **BREAKING** `specworks harness` takes no `REQUEST` argument and no
  `--change` option any more. It opens the chat, always empty. Nothing is said
  for the user: a change starts, or continues, when the user sends a peer a
  message (`@refine <request>`, `@build go on with add-x`).
- A run's conversation is written to the first active change whose folder
  changes during the run (created during the run or not); a new run no longer
  loads an earlier conversation.
- The code that said the request for the user goes: the first-message logic of
  the harness session and `first_peer()`.
- Unchanged: the extra and key errors, every peer behaviour.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`: REQ-CLI-022 (no `REQUEST`, no `--change`; AC-CLI-022.3 and .4
  retired; .6 the chat opens with nothing said; .7 no change option).
- `harness`: REQ-HARNESS-009 (a run starts empty; its change is the first one
  whose folder changes; AC-HARNESS-009.3 retired; .2 reworded; .5 added).

## Related requirements

- REQ-CLI-022 modified.
- REQ-HARNESS-009 modified (the run's change; no reload at start).
- REQ-HARNESS-003 left: AC-HARNESS-003.1's "the user's request reaches
  `refine`" is the user's message in the chat, which still holds.
- REQ-HARNESS-001, -002, -004 to -008, -010 left: no peer behaviour changes.
- REQ-CLI-002 left: `specworks harness` no longer names a change.

## Impact

- `src/specworks/cli/harness.py` (the argument), `src/specworks/harness/session.py`
  (`build_harness`, `run_harness`, the session's first message, `first_peer`),
  `src/specworks/harness/backend.py` (finding the run's change, no load).
- `tests/cli/test_harness.py` and the harness tests that build a session with a
  request.

## Out of Scope

- A friendly message for a leftover argument: `specworks harness "add x"` gets
  the command line's own usage error.
- Choosing which earlier conversation to load: a run always starts empty.
