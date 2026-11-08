# Proposal: harness-chat-only

## Why

`specworks harness "<request>"` sends the request to `refine` (or to the peer of
the change's phase) as the user's first message. That is a second way to do
what the chat already does: typing `@refine <request>` starts a change. The user
asked for one way only: opening the harness opens the chat.

## What Changes

- **BREAKING** `specworks harness` takes no `REQUEST` argument any more. It
  opens the chat; with `--change REF` it opens that change's conversation, as
  before. Nothing is said for the user: a new change starts when the user sends
  `@refine <request>`.
- The code that said the request for the user goes: the first-message logic of
  the harness session and `first_peer()`.
- Unchanged: the extra and key errors, `--change`, every peer behaviour.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`: REQ-CLI-022 (no `REQUEST`; AC-CLI-022.3 retired; AC-CLI-022.4 without
  a request; AC-CLI-022.6 added: the chat opens with nothing said).
- `harness`: REQ-HARNESS-009 (AC-HARNESS-009.2 starts from the user's first
  message instead of a request given on the command line).

## Related requirements

- REQ-CLI-022 modified.
- REQ-HARNESS-009 modified (wording of AC-HARNESS-009.2).
- REQ-HARNESS-003 left: AC-HARNESS-003.1's "the user's request reaches
  `refine`" is the user's message in the chat, which still holds.
- REQ-HARNESS-001, -002, -004 to -008, -010 left: no peer behaviour changes.
- REQ-CLI-002 left: `--change` still resolves a change the same way.

## Impact

- `src/specworks/cli/harness.py` (the argument), `src/specworks/harness/session.py`
  (`build_harness`, `run_harness`, the session's first message, `first_peer`).
- `tests/cli/test_harness.py` and the harness tests that build a session with a
  request.

## Out of Scope

- A friendly message for a leftover argument: `specworks harness "add x"` gets
  the command line's own usage error.
- Removing `--change` (kept, by the user's choice).
