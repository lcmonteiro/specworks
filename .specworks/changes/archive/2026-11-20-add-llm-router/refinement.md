# Refinement: add-llm-router

## Problem

In `specworks harness`, a message the user types without `@<peer>` reaches no
one: with 17 skill peers, chatinho's `SimpleRouter` finds no single peer to
answer it, so it goes unanswered. Users must know the peer names and address
every new request by hand. chatinho now ships an `LLMRouter` (pinned at
`ff18f15`) that asks a model which peer a message is for, so the harness can
pick the peer itself.

## Outcomes

- A message with no `@<peer>` is answered by the skill peer that fits it best
  (e.g. "let users reset passwords" reaches `refine`), chosen from the peers'
  descriptions and the recent conversation.
- When the router cannot decide (no clear peer, the model fails, times out or
  names no peer), the message is answered by `onboard`, which says where the
  project stands and what to run next: an unaddressed message is never left
  unanswered.
- The user configures nothing new: routing works with the same model settings
  and Copilot login the peers already use.
- `@<peer>` messages, replies to a peer and hand-overs behave as today.

## Context

**Observed:**
- `src/specworks/harness/session.py` builds the `ChatSession` with
  `router=SimpleRouter()`, and the peers with `model_from_env()`
  (`model.py`): `SPECWORKS_MODEL_*`, `harness.model`, or a Copilot login
  (REQ-HARNESS-010, -012, -013).
- `SimpleRouter` sends a reply to the author of what it replies to, and
  anything else only when exactly one peer answers.
- chatinho's `LLMRouter` (`chatinho/routers/llm.py`) applies those rules first,
  then asks a model with each candidate's name and `description` and the last
  6 messages. It answers one name or `everyone`; anything unusable (timeout,
  unknown name, no key, API error) is logged and returns None (a broadcast).
  It takes an `Endpoint` (base URL, model, key; the key may be a callable, so
  a renewing Copilot session token fits) and builds its own `AsyncOpenAI`
  client, with no way to add request headers.
- `LLMRouter` needs the `chatinho[openai]` extra; `openai` is installed today
  only transitively.
- The skill peers (`harness/peers/*.py`) use `@connector("<name>")` with no
  `description`, so a model would see bare names.
- A skill peer's `listen` does nothing (REQ-HARNESS-003), so a broadcast wakes
  no skill peer: today a failed choice would leave the message unanswered.
- Copilot requests carry `EDITOR_HEADERS` (`harness/copilot.py`).

**Assumed:**
- The Copilot API rejects chat requests without the `Editor-Version` header,
  so `LLMRouter` as it is would always fail with a Copilot login (not checked
  here: no login in this environment).

## Constraints

- [hard] No key or token in any log, error, reply or `chat.jsonl`
  (REQ-HARNESS-010, -012).
- [hard] A failed routing call never stops the chat.
- [hard] Routing uses the peers' model and key, including the Copilot login
  and its token renewal.
- [soft] No private chatinho API used from specworks.
- [soft] No new setting for the user.

## Options

### Option A: LLMRouter as it is

Use `LLMRouter` with an `Endpoint` built from the peers' settings, wrapped so
that None becomes `onboard`; add peer descriptions.

- **Pros:** smallest; no chatinho change.
- **Cons:** with a Copilot login every choice likely fails (no headers).
- **Effort:** S
- **Touches:** `harness`
- **Outcomes:** meets all for a key from the environment; fails "best peer" for
  Copilot users (always `onboard`).

### Option B: Subclass LLMRouter in specworks

Override its private client methods to add the Copilot headers.

- **Pros:** meets every outcome now, no cross-repo step.
- **Cons:** tied to chatinho internals; breaks on any pin bump.
- **Effort:** S
- **Touches:** `harness`
- **Outcomes:** meets all.

### Option C: Headers in chatinho first, then LLMRouter

Change chatinho so `LLMRouter` (or `Endpoint`) accepts extra request headers,
bump the pin, then do Option A passing `EDITOR_HEADERS` for a Copilot login.

- **Pros:** meets every outcome on chatinho's own router, public API only;
  the fix benefits any chatinho user behind a header-requiring endpoint.
- **Cons:** needs a chatinho change and release before this one can build.
- **Effort:** M (S in chatinho, S here)
- **Touches:** `harness` (and chatinho upstream)
- **Outcomes:** meets all.

### Option D: A specworks router on the peers' model

A small router in specworks using chatinho's public `simple_route` and
`answering`, then one call to the peers' own LangChain model.

- **Pros:** meets every outcome now; headers and token renewal come with the
  model object.
- **Cons:** duplicates `LLMRouter`'s prompt and parsing (~60 lines); does not
  reuse chatinho's router.
- **Effort:** S-M
- **Touches:** `harness`
- **Outcomes:** meets all.

## Recommendation

Option C, agreed with the user: extend chatinho's `LLMRouter` to send extra
headers, bump the pin, then route the harness with it, using the peers' model
and key, `EDITOR_HEADERS` with a Copilot login, a description per skill peer,
and `onboard` when the router chooses no one.

## Open Questions

- Where the headers go in chatinho: an `LLMRouter` argument or an `Endpoint`
  field. (who can answer: the chatinho maintainer, in the chatinho change)
- Whether each peer's description comes from its skill's front matter
  `description` (no duplicated text) or is written per peer. (who can answer:
  the user, at specify)
- Whether to declare the `chatinho[openai]` extra explicitly in
  `pyproject.toml`. (who can answer: the user, at specify)

## Candidate Capabilities

- `harness`: modified - unaddressed messages routed by `LLMRouter` on the
  peers' model, a description per skill peer, and `onboard` as the fallback.
