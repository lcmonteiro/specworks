# Design: update-chatinho

## Context

A dependency bump: the chatinho pin moves to `57a1b98` and one test fixture
follows chatinho's move of the router's client. See proposal.md.

## Decisions

### Patch the client where chatinho now builds it

`LLMRouter` no longer imports `AsyncOpenAI` in `chatinho.routers.llm`; the
client is built in `chatinho.support.kits.model.endpoint`, so the fixture in
`tests/harness/test_router.py` patches it there. Alternative considered:
patching `openai.AsyncOpenAI` itself, which would also catch every other
client built during the test; rejected as wider than the test needs.

## Interfaces

None: no public API of specworks is added or changed. The change only moves a
dependency pin and a test fixture; no file under `src/specworks` changes.

## Diagrams

No structural change.

## Risks / Trade-offs

- [chatinho changes an import path the harness uses] -> the old
  `chatinho.support.parts.keys.endpoint` path still exists at `57a1b98`, and
  the full suite, ruff and mypy are the check (task 3.1).
