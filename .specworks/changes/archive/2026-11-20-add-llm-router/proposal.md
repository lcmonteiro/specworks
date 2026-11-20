# Proposal: add-llm-router

## Why

In `specworks harness` a message typed without `@<peer>` reaches no one: with
17 skill peers, `SimpleRouter` finds no single peer to answer it. chatinho now
ships an `LLMRouter` that asks a model which peer a message is for; the harness
should use it, so a plain request reaches the right skill, and never goes
unanswered.

## What Changes

- The harness session routes with chatinho's `LLMRouter` instead of
  `SimpleRouter`: a message that names no peer, and does not reply to one, is
  answered by the skill peer the model picks.
- When the router picks no one (the model answers `everyone`, names no peer,
  fails, has no key or times out), the peer `onboard` answers.
- The router asks with the peers' own model, base URL and key, a stored
  Copilot login included (its renewed session token and Copilot's editor
  headers), so there is nothing new to configure.
- Each skill peer gets a description, its skill's front matter
  `description`, which the router gives the model.
- Precondition (outside this repo): chatinho's `LLMRouter` gains a way to send
  extra request headers; the chatinho pin moves to that commit, and the
  `harness` extra declares `chatinho[openai]`, which `LLMRouter` needs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `harness`: adds routing of unaddressed messages (REQ-HARNESS-014), the
  router's model (REQ-HARNESS-015) and a description per skill peer
  (REQ-HARNESS-016).

## Related requirements

- REQ-HARNESS-001 left: the peers, their names and instructions are unchanged; the description is a new requirement (REQ-HARNESS-016).
- REQ-HARNESS-002 left: a peer's run, tools and memory are unchanged.
- REQ-HARNESS-003 left: a routed message arrives addressed to the chosen peer (chatinho sets its addressee), so "a say addressed to it" already covers it; hand-overs always name their peer.
- REQ-HARNESS-004 left: the preamble and `ask_user` are unchanged.
- REQ-HARNESS-005 left: `@<peer>` still goes to that peer, without the router.
- REQ-HARNESS-008 left: `ws_run`'s environment is unrelated to routing.
- REQ-HARNESS-010 left: how the model and key are found is unchanged; REQ-HARNESS-015 reuses it.
- REQ-HARNESS-011 left: the login flow is unchanged.
- REQ-HARNESS-012 left: the login's key and renewal are unchanged; REQ-HARNESS-015 reuses them.
- REQ-HARNESS-013 left: the default model choice is unchanged; the router uses the model it gives.
- REQ-CLI-003, REQ-CLI-009, REQ-CLI-013, REQ-CLI-022, REQ-CLI-023 left: the commands and their output do not change.
- REQ-INTEG-004, REQ-INTEG-005, REQ-INTEG-006 left: installing the skills is unchanged; their `description` is only read.
- REQ-PROJ-003, REQ-PROJ-004, REQ-PROJ-008, REQ-PROJ-022, REQ-PROJ-035 left: config and capabilities are unchanged (no new config key).
- REQ-SPECS-004, REQ-SPECS-005, REQ-FLOW-010, REQ-FLOW-012, REQ-FLOW-016, REQ-FLOW-018, REQ-FLOW-019, REQ-CLI-011, REQ-CLI-024 left: "route" and "description" there are about findings and spec text, not the chat.

## Impact

- Code: `src/specworks/harness/session.py` (the router), `model.py` (the
  router's endpoint from the same settings), `peers/base.py` (descriptions),
  a small wrapper for the `onboard` fallback.
- Dependencies: chatinho pin bumped to a commit whose `LLMRouter` sends extra
  headers; `chatinho[openai]` in the `harness` extra and dev group.
- Cost: one short model call (16 tokens out) per unaddressed message with two
  or more candidate peers; none for `@<peer>` messages, replies or hand-overs.
- Assumptions: a peer's description is its skill's whole front matter
  `description` (one source, no duplicated text); the router keeps chatinho's
  defaults (last 6 messages, 10 s timeout).

## Out of Scope

- Changing `@<peer>` addressing, replies or hand-overs.
- A separate model, key or setting for the router.
- Telling the user which peer the router picked, beyond that peer's answer.
- The chatinho change itself, which is made in chatinho.
